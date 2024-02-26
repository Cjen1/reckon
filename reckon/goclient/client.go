package rc_go

import (
	"fmt"
	"log"
	"os"
	"time"
	"bufio"
	"io"
	"encoding/binary"
	"encoding/json"
	"sync"
)

func unix_seconds(t time.Time) float64 {
	return float64(t.UnixNano()) / 1e9
}

type Client interface {
	Put(string, string) (string, error)
	Get(string) (string, string, error)
	Close ()
}

type jsonmap = map[string]interface{}

type Operation struct {
	Payload map[string]string `json:"payload"`
	Time float64 `json:"time"`
}

func decode_operation(m jsonmap) Operation {
	var res Operation
	payload := make(map[string]string)
	for key, value := range m {
		switch key {
		case "payload":
			for k,v := range value.(map[string]interface{}) {
				payload[k] = v.(string)
			}
			res.Payload = payload
		case "time":
			res.Time = value.(float64)
		default:
			log.Fatal("Cannot parse operation: %v", m)
			panic("Failed to parse packet")
		}

	}
	return res
}

type Preload struct {
	Prereq bool `json:"prereq"`
	Operation Operation `json:"operation"`
}

func decode_preload(m jsonmap) Preload {
	var res Preload
	for key, value := range m {
		switch key {
		case "prereq":
			res.Prereq = value.(bool)
		case "operation":
			res.Operation = decode_operation(value.(jsonmap))
		case "kind":
		default:
			log.Fatal("Cannot parse preload: %v", m)
			panic("Failed to parse packet")
		}
	}
	return res
}

func response(
	t_submitted float64,
	t_result float64,
	result string,
	kind string,
	clientid string,
	other jsonmap) jsonmap {
	return map[string]interface{}{
		"kind": "result",
		"t_submitted": t_submitted,
		"t_result": t_result,
		"result": result,
		"op_kind": kind,
		"clientid": clientid,
		"other": other,
	}
}

func put(cli Client, key string, value string, clientid string, expected_start float64) jsonmap{
	st := unix_seconds(time.Now())
	target, err := cli.Put(key, value)
	end := unix_seconds(time.Now())

	err_msg := "Success"
	if err != nil {
		err_msg = err.Error()
	}

	resp := response(st, end, err_msg, "write", clientid, map[string]interface{}{
		"target": target,
		"expected_start": expected_start,
	})

	return resp
}

func get(cli Client, key string, clientid string, expected_start float64) jsonmap{
	st := unix_seconds(time.Now())
	_, target, err := cli.Get(key)
	end := unix_seconds(time.Now())

	err_msg := "Success"
	if err != nil {
		err_msg = err.Error()
	}

	resp := response(st, end, err_msg, "read", clientid, map[string]interface{}{
		"target": target,
		"expected_start": expected_start,
	})

	return resp
}

func check(e error, s string) {
	if e != nil {
		log.Fatal("Fatal error: %s: %v",s, e)
	}
}

func perform(op Operation, cli Client, clientid string, test_start_time float64, new_client_per_request bool, client_gen func () (Client, error)) jsonmap {
	//Create a new client if desired
	func_cli := &cli
	if new_client_per_request {
		cli, err := client_gen()
		check(err, "generating client")
		defer cli.Close()
		func_cli = &cli
	}

	expected_start := op.Time + test_start_time
	switch op.Payload["kind"] {
	case "write":
		return put(*func_cli, op.Payload["key"], op.Payload["value"], clientid, expected_start)
	case "read":
		return get(*func_cli, op.Payload["key"], clientid, expected_start)
	default:
		return response(
			-1.0,
			-1.0,
			fmt.Sprintf("Error operation (%v) was not found or supported", op),
			op.Payload["kind"],
			clientid,
			nil)
	}
}

func recv(reader *bufio.Reader) jsonmap {
	var size int32
	if err := binary.Read(reader, binary.LittleEndian, &size); err != nil {
		log.Fatal(err)
	}

	payload := make([]byte, size)
	if _, err := io.ReadFull(reader, payload); err != nil {
		log.Fatal(err)
	}

	var msg map[string]interface{}
	json.Unmarshal(payload, &msg)

	return msg

}

func send(msg jsonmap) {
	payload, err := json.Marshal(msg)
	check(err, "marshalling json")

	var size int32
	size = int32(len(payload))
	size_part := make([]byte, 4)
	binary.LittleEndian.PutUint32(size_part, uint32(size))

	output := append(size_part[:], payload[:]...)
	_, err = os.Stdout.Write(output)
	check(err, "writing packet")
}

func init() {
	log.SetOutput(os.Stderr)
}

func result_loop(res_ch chan jsonmap, done chan struct{}) {
	var results []jsonmap
	log.Print("Starting result loop")
	for res := range res_ch {
		results = append(results, res)
	}

	log.Print("Got all results, writing to load generator")
	for _, res := range results {
		send(res)
	}
	close(done)
}

func waitGroupChannel(wg *sync.WaitGroup) (<-chan struct{}) {
	complete := make(chan struct{})
	go func() {
		wg.Wait()
		close(complete)
	} ()
	return complete
}

// Buffering channel, to force delayed clients to quit
func make_messenger(input <-chan jsonmap, output chan jsonmap) chan struct{}{
	close_this := make(chan struct{})
	go func(messenger_close chan struct {}, input <-chan jsonmap, output chan jsonmap) {
		for {
			select {
			case <- close_this:
				close(output)
				return
			case result := <-input:
				output <- result
			}
		}
	}(close_this, input, output)
	return close_this
}

func Run(client_gen func() (Client, error), clientid string, new_client_per_request bool) {
	log.Print("Client: Starting run")

	cli, err := client_gen()
	defer cli.Close()
	check(err, "create client")

	reader := bufio.NewReader(os.Stdin)

	//Phase 1: preload
	log.Print("Phase 1: preload")
	var ops []Operation
	got_finalise := false
	for !got_finalise {
		op := recv(reader)

		switch op["kind"] {
		case "preload":
			preload := decode_preload(op)
			if preload.Prereq {
				perform(preload.Operation, cli, clientid, unix_seconds(time.Now()), false, client_gen)
			} else {
				ops = append(ops, preload.Operation)
			}
		case "finalise":
			got_finalise = true
		default:
			log.Print("Got unrecognised message...")
			log.Print(op)
			log.Fatal("Quitting due to unrecognised message")
		}
	}

	//Phase 2: Readying
	log.Print("Phase 2: Readying")

	//Dispatch results loop
	final_res_ch := make(chan jsonmap)
	results_complete := make(chan struct{})
	go result_loop(final_res_ch, results_complete)
	res_ch := make(chan jsonmap, 50000)
	messenger_complete := make_messenger(res_ch, final_res_ch)

	//signal ready
	log.Print("Sending ready")
	send(map[string]interface{}{"kind": "ready"})
	log.Print("Sent ready")

	got_start := false
	for !got_start{
		op := recv(reader)
		switch op["kind"]{
		case "start":
			log.Print("Got start_request")
			got_start = true
		default:
			log.Fatal("Got a message which wasn't a start!")
		}
	}

	//Phase 3: Execute
	log.Print("Phase 3: Execute")
	var wg_perform sync.WaitGroup
	stopCh := make(chan struct{})
	op_ch := make(chan Operation)
	log.Print("Starting to perform ops")
	start_time := time.Now()
	for _, op := range ops {
		end_time := start_time.Add(time.Duration(op.Time * float64(time.Second)))
		t := time.Now()
		time.Sleep(end_time.Sub(t))

		select {
		case op_ch <- op:
			continue
		default:
			wg_perform.Add(1)
			//If can't start op currently create a new worker to do so
			go func(op_ch <-chan Operation, wg *sync.WaitGroup) {
				defer wg.Done()
				for op := range op_ch {
					resp := perform(op, cli, clientid, unix_seconds(start_time), new_client_per_request, client_gen)
					select {
					case <- stopCh:
						continue
					case res_ch <- resp:
					}
				}
			} (op_ch, &wg_perform)
			op_ch <- op
		}
	}
	log.Print("Finished sending ops")
	log.Print("Phase 4: Collate")

	// Tell threads that there are no more ops
	close(op_ch)

	select {
	case <- waitGroupChannel(&wg_perform):
	case <- time.After(30 * time.Second):
	}

	// Cut off trailing results
	close(stopCh)


	log.Print("Closing result pipe")
	//Signal end of results and force any remaining clients to not write to it
	close(messenger_complete)

	log.Print("Waiting for results to be sent")
	//Wait for results to be returned to generator
	<-results_complete
	send(map[string]interface{}{"kind":"finished"})
	log.Print("Results sent, exiting")
  os.Exit(0)
}
