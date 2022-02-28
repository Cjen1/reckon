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
	Kind string `json:"kind"`
	Payload map[string]string `json:"payload"`
	Time float64 `json:"time"`
}

func decode_operation(m jsonmap) Operation {
	var res Operation
	for key, value := range m {
		switch key {
		case "kind":
			res.Kind = value.(string)
		case "payload":
			res.Payload = value.(map[string]string)
		case "time":
			res.Time = value.(float64)
		default:
			log.Fatal("Cannot parse: %v", m)
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
		default:
			log.Fatal("Cannot parse: %v", m)
			panic("Failed to parse packet")
		}
	}
	return res
}

type Message struct {
	Kind string `json:"kind"`
	Payload jsonmap `json:"payload"`
}

func response(
	t_submitted float64,
	t_result float64,
	result string,
	kind string,
	clientid string,
	other jsonmap) jsonmap {
	return map[string]interface{}{
		"t_submitted": t_submitted,
		"t_result": t_result,
		"result": result,
		"kind": kind,
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

func check(e error) {
	if e != nil {
		log.Fatal(e)
	}
}

func perform(op Operation, cli Client, clientid string, test_start_time float64, new_client_per_request bool, client_gen func () (Client, error)) jsonmap {
	//Create a new client if desired
	func_cli := &cli
	if new_client_per_request {
		cli, err := client_gen()
		check(err)
		defer cli.Close()
		func_cli = &cli
	}

	expected_start := op.Time + test_start_time
	switch op.Kind {
	case "write":
		return put(*func_cli, op.Payload["key"], op.Payload["value"], clientid, expected_start)
	case "read":
		return get(*func_cli, op.Payload["key"], clientid, expected_start)
	default:
		return response(
			-1.0,
			-1.0,
			fmt.Sprintf("Error operation (%v) was not found or supported", op),
			op.Kind,
			clientid,
			nil)
	}
}

func recv(reader *bufio.Reader) Message {
	var size int32
	if err := binary.Read(reader, binary.LittleEndian, &size); err != nil {
		log.Fatal(err)
	}

	payload := make([]byte, size)
	if _, err := io.ReadFull(reader, payload); err != nil {
		log.Fatal(err)
	}

	var msg Message
	json.Unmarshal(payload, &msg)

	return msg

}

func send(msg Message) {
	payload, err := json.Marshal(msg)
	check(err)

	var size int32
	size = int32(len(payload))
	size_part := make([]byte, 4)
	binary.LittleEndian.PutUint32(size_part, uint32(size))

	output := append(size_part[:], payload[:]...)
	_, err = os.Stdout.Write(output)
	check(err)
}

func init() {
	log.SetOutput(os.Stderr)
	log.SetFlags(log.Ltime | log.Lmicroseconds)
}

func result_loop(res_ch chan jsonmap, done chan struct{}) {
	var results []jsonmap
	log.Print("Starting result loop")
	for res := range res_ch {
		results = append(results, res)
	}

	log.Print("Got all results, writing to load generator")
	for _, res := range results {
		msg := Message{
			Kind : "result",
			Payload : res,
		}
		send(msg)
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
	check(err)

	reader := bufio.NewReader(os.Stdin)

	//Phase 1: preload
	log.Print("Phase 1: preload")
	var ops []Operation
	got_finalise := false
	for !got_finalise {
		op := recv(reader)

		switch op.Kind {
		case "preload":
			preload := decode_preload(op.Payload)
			if preload.Prereq {
				log.Print("Performing prereq")
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
	send(Message{Kind:"ready", Payload : nil})

	//Phase 3: Execute
	log.Print("Phase 3: Execute")
	got_start := false
	for !got_start{
		op := recv(reader)
		switch op.Kind{
		case "start":
			log.Print("Got start_request")
			got_start = true
		default:
			log.Fatal("Got a message which wasn't a start!")
		}
	}

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
	close(stopCh)
	close(op_ch)

	select {
	case <- waitGroupChannel(&wg_perform):
	case <- time.After(30 * time.Second):
	}

	log.Print("Closing result pipe")
	//Signal end of results and force any remaining clients to not write to it
	close(messenger_complete)

	log.Print("Waiting for results to be sent")
	//Wait for results to be returned to generator
	<-results_complete
	log.Print("Results sent, exiting")
}
