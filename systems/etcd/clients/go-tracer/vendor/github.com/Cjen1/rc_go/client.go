package rc_go

import (
	"fmt"
	"log"
	"os"
	"time"
	"bufio"
	"io"
	"encoding/binary"
	"sync"

	"github.com/Cjen1/rc_go/OpWire"
	"github.com/golang/protobuf/proto"
)

func unix_seconds(t time.Time) float64 {
	return float64(t.UnixNano()) / 1e9
}

type Client interface {
	Put(string, string) error
	Get(string) (string, error)
	Close ()
}

func put(cli Client, op *OpWire.Request_Operation_Put, clientid uint32, expected_start float64) *OpWire.Response{
	st := unix_seconds(time.Now())
	var err error
	if true {
		err = cli.Put(string(op.Put.Key), string(op.Put.Value))
	}
	end := unix_seconds(time.Now())

	err_msg := "None"
	if err != nil {
		err_msg = "ERROR WAS FOUND: " + err.Error()
	}

	resp := &OpWire.Response{
		ResponseTime: end - expected_start,
		Err:          err_msg,
		ClientStart:  st,
		QueueStart:   expected_start,
		End:          end,
		Clientid:     clientid,
		Optype:       "Write",
	}

	return resp
}

func get(cli Client, op *OpWire.Request_Operation_Get, clientid uint32, expected_start float64) *OpWire.Response{
	st := unix_seconds(time.Now())
	_, err := cli.Get(string(op.Get.Key))
	end := unix_seconds(time.Now())

	err_msg := "None"
	if err != nil {
		err_msg = "ERROR WAS FOUND: " + err.Error()
	}

	resp := &OpWire.Response{
		ResponseTime: end - expected_start,
		Err:          err_msg,
		ClientStart:  st,
		QueueStart:   expected_start,
		End:          end,
		Clientid:     clientid,
		Optype:       "Read",
	}

	return resp
}

func check(e error) {
	if e != nil {
		log.Fatal(e)
	}
}

func perform(op OpWire.Request_Operation, cli Client, clientid uint32, start_time float64, new_client_per_request bool, client_gen func () (Client, error)) *OpWire.Response{
	//Create a new client if desired
	//func_cli := &cli
	//if new_client_per_request {
	//	cli, err := client_gen()
	//	check(err)
	//	defer cli.Close()
	//	func_cli = &cli
	//}

	//expected_start := op.Start + start_time
	//switch op_t := op.OpType.(type) {
	//case *OpWire.Request_Operation_Put:
	//	return put(*func_cli, op_t, clientid, expected_start)
	//case *OpWire.Request_Operation_Get:
	//	return get(*func_cli, op_t, clientid, expected_start)
	switch {
	default:
		resp := &OpWire.Response{
			ResponseTime: -1,
			Err:          fmt.Sprintf("Error: Operation (%v) was not found / supported", op),
			Clientid:     clientid,
			Optype:       "Error",
		}
		return resp
	}
}

func recv(reader *bufio.Reader) *OpWire.Request{
	var size int32
	if err := binary.Read(reader, binary.LittleEndian, &size); err != nil {
		log.Fatal(err)
	}

	payload := make([]byte, size)
	if _, err := io.ReadFull(reader, payload); err != nil {
		log.Fatal(err)
	}

	op := &OpWire.Request{}
	if err := proto.Unmarshal([]byte(payload), op); err != nil {
		log.Fatal("Failed to parse incomming operation")
	}
	return op
}

func marshall_response(resp *OpWire.Response) []byte {
	payload, err := proto.Marshal(resp)
	check(err)
	return payload
}

func send(writer *os.File, msg []byte){
	var size int32
	size = int32(len(msg))
	size_part := make([]byte, 4)
	// uint32 doesn't change sign bit, just how value is interpreted
	binary.LittleEndian.PutUint32(size_part, uint32(size))

	payload := append(size_part[:], msg[:]...)
	_, err := writer.Write(payload)
	check(err)
}

func init() {
	log.SetOutput(os.Stderr)
	log.SetFlags(log.Ltime | log.Lmicroseconds)
}

func result_loop(res_ch chan *OpWire.Response, out *os.File, done chan struct{}) {
	var results []*OpWire.Response
	log.Print("Starting result loop")
	for res := range res_ch {
		results = append(results, res)
	}

	log.Print("Got all results, writing to load generator")
	for _, res := range results {
		payload := marshall_response(res)
		send(out, payload)
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

func make_messenger(input <-chan *OpWire.Response, output chan *OpWire.Response) chan struct{}{
	close_this := make(chan struct{})
	go func(messenger_close chan struct {}, input <-chan *OpWire.Response, output chan *OpWire.Response) {
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

func Run(client_gen func() (Client, error), clientid uint32, result_pipe string, new_client_per_request bool) {
	log.Print("Client: Starting run")
	log.Printf("Client: creating file")
	log.Print(result_pipe)
	file, err := os.OpenFile(result_pipe, os.O_WRONLY, 0755)
	check(err)
	defer file.Close()
	out_writer := file

	cli, err := client_gen()
	defer cli.Close()
	check(err)

	reader := bufio.NewReader(os.Stdin)

	//Phase 1: preload
	log.Print("Phase 1: preload")
	var ops []*OpWire.Request_Operation
	got_finalise := false
	for !got_finalise {
		op := recv(reader)
		log.Print(op)

		switch op.Kind.(type) {
		case *OpWire.Request_Op:
			if op.GetOp().Prereq {
				log.Print("Performing prereq")
				perform(*op.GetOp(), cli, clientid, unix_seconds(time.Now()), false, client_gen)
			} else {
				ops = append(ops, op.GetOp())
			}
		case *OpWire.Request_Finalise_:
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
	final_res_ch := make(chan *OpWire.Response)
	results_complete := make(chan struct{})
	go result_loop(final_res_ch, out_writer, results_complete)
	res_ch := make(chan *OpWire.Response, 50000)
	messenger_complete := make_messenger(res_ch, final_res_ch)

	//signal ready
	send(out_writer, []byte(""))

	//Phase 3: Execute
	log.Print("Phase 3: Execute")
	got_start := false
	for !got_start{
		op := recv(reader)
		switch op.Kind.(type) {
		case *OpWire.Request_Start_:
			log.Print("Got start_request")
			got_start = true
		default:
			log.Fatal("Got a message which wasn't a start!")
		}
	}

	var wg_perform sync.WaitGroup
	op_ch := make(chan *OpWire.Request_Operation)
	log.Print("Starting to perform ops")
	start_time := time.Now()
	for _, op := range ops {
		end_time := start_time.Add(time.Duration(op.Start * float64(time.Second)))
		t := time.Now()
		time.Sleep(end_time.Sub(t))

		select {
		case op_ch <- op:
			continue
		default:
			wg_perform.Add(1)
			//If can't start op currently create a new worker to do so
			go func(op_ch <-chan *OpWire.Request_Operation, wg *sync.WaitGroup) {
				for op := range op_ch {
					resp := perform(*op, cli, clientid, unix_seconds(start_time), new_client_per_request, client_gen)
					res_ch <- resp
				}
				wg.Done()
			} (op_ch, &wg_perform)
			op_ch <- op
		}
	}
	log.Print("Finished sending ops")
	log.Print("Phase 4: Collate")
	close(op_ch)

	log.Print("Waiting for ops to finish")
	wg_perform.Wait()

	log.Print("Closing result pipe")
	//Signal end of results 
	close(messenger_complete)

	log.Print("Waiting for results to be sent")
	//Wait for results to be returned to generator
	<-results_complete
	log.Print("Results sent, exiting good night")
}
