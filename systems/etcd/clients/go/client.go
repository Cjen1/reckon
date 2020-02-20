package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"
	"time"
	"bufio"
	"io"
	"encoding/binary"
	"sync"

	"client/OpWire"
	"github.com/golang/protobuf/proto"
	"go.etcd.io/etcd/clientv3"
)

func unix_seconds(t time.Time) float64 {
	return float64(t.UnixNano()) / 1e9
}

func put(res_ch chan *OpWire.Response, cli *clientv3.Client, op *OpWire.Request_Operation_Put, clientid uint32, start float64) {
	// TODO implement options
	st := unix_seconds(time.Now())
	var err error
	if true {
		_, err = cli.Put(context.Background(), string(op.Put.Key), string(op.Put.Value))
	}
	end := unix_seconds(time.Now())

	err_msg := "None"
	if err != nil {
		_, err = cli.Put(context.Background(), string(op.Put.Key), string(op.Put.Value))
		if err != nil {
			err_msg = "ERROR WAS FOUND: " + err.Error()
		}
	}

	resp := &OpWire.Response{
		ResponseTime: end - start,
		Err:          err_msg,
		ClientStart:  st,
		QueueStart:   start,
		End:          end,
		Clientid:     clientid,
		Optype:       "Write",
		Target:       cli.ActiveConnection().Target(),
	}

	//log.Print("CLIENT: Successfully put")

	res_ch <- resp
}

func get(res_ch chan *OpWire.Response, cli *clientv3.Client, op *OpWire.Request_Operation_Get, clientid uint32, start float64) {
	st := unix_seconds(time.Now())
	_, err := cli.Get(context.Background(), string(op.Get.Key))
	end := unix_seconds(time.Now())

	err_msg := "None"
	if err != nil {
		err_msg = "ERROR WAS FOUND: " + err.Error()
	}

	resp := &OpWire.Response{
		ResponseTime: end - start,
		Err:          err_msg,
		ClientStart:  st,
		QueueStart:   start,
		End:          end,
		Clientid:     clientid,
		Optype:       "Read",
		Target:       cli.ActiveConnection().Target(),
	}

	//log.Print("CLIENT:Successfully got")

	res_ch <- resp
}

func check(e error) {
	if e != nil {
		log.Fatal(e)
	}
}

func perform(op *OpWire.Request_Operation, res_ch chan *OpWire.Response, cli *clientv3.Client, clientid uint32, start_time time.Time) {
	//defer wg.Done()

	start := op.Start + unix_seconds(start_time)
	switch op_t := op.OpType.(type) {
	case *OpWire.Request_Operation_Put:
		//log.Print("Putting")
		put(res_ch, cli, op_t, clientid, start)
		//log.Print("Put")
	case *OpWire.Request_Operation_Get:
		//log.Print("Getting")
		get(res_ch, cli, op_t, clientid, start)
		//log.Print("Got")
	default:
		resp := &OpWire.Response{
			ResponseTime: -1,
			Err:          fmt.Sprintf("Error: Operation (%v) was not found / supported", op),
			Clientid:     clientid,
			Optype:       "Error",
		}
		res_ch <- resp
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
	log.Printf("received op size = %d\n", size)
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
	log.Printf("send size = %L", size)
	size_part := make([]byte, 4)
	binary.LittleEndian.PutUint32(size_part, uint32(size))

	payload := append(size_part[:], msg[:]...)
	_, err := writer.Write(payload)
	check(err)
}

func init() {
	log.SetOutput(os.Stderr)
	log.SetFlags(log.Ltime | log.Lmicroseconds)
}

func result_loop(res_ch chan *OpWire.Response, out *os.File, done chan bool) {
	var results []*OpWire.Response
	log.Print("Starting result loop")
	for res := range res_ch {
		results = append(results, res)
	}

	for _, res := range results {
		payload := marshall_response(res)
		log.Print("Sending response")
		send(out, payload)
	}
	done <- true
}

func consume_ignore(res_ch chan *OpWire.Response) {
	for range res_ch {}
}

func main() {
	log.Print("Client: Starting client")

	endpoints := strings.Split(os.Args[1], ",")
	log.Printf("%v\n", endpoints)

	i, err := strconv.ParseUint(os.Args[2], 10, 32)
	check(err)
	clientid := uint32(i)

	//num_channels := 1000

	log.Printf("Client: creating file")
	result_pipe := os.Args[3]
	log.Print(result_pipe)
	file, err := os.OpenFile(result_pipe, os.O_WRONLY, 0755)
	check(err)
	defer file.Close()
	out_writer := file

	dialTimeout := 2 * time.Second

	cli, err := clientv3.New(clientv3.Config{
		Endpoints:            endpoints,
		DialTimeout:          dialTimeout,
		DialKeepAliveTime:    dialTimeout / 2,
		DialKeepAliveTimeout: dialTimeout * 2,
		AutoSyncInterval:     dialTimeout / 2,
	})
	defer cli.Close()
	check(err)

	reader := bufio.NewReader(os.Stdin)

	//Phase 1: preload
	log.Print("Phase 1: preload")
	var ops []*OpWire.Request_Operation
	//var wg_prereq sync.WaitGroup
	got_finalise := false
	bh_ch := make(chan *OpWire.Response)
	go consume_ignore(bh_ch)
	for !got_finalise {
		op := recv(reader)
		log.Print(op)

		switch op.Kind.(type) {
		case *OpWire.Request_Op:
			if op.GetOp().Prereq {
				log.Print("Performing prereq")
				//wg_prereq.Add(1)
				perform(op.GetOp(), bh_ch, cli, clientid, time.Now())
			} else {
				ops = append(ops, op.GetOp())
			}
		case *OpWire.Request_Finalise_:
			got_finalise = true
		default:
			log.Fatal("Got unrecognised message...")
		}
	}

	//Phase 2: Readying
	log.Print("Phase 2: Readying")
	//wg_prereq.Wait()
	close(bh_ch)

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

	//var wg_chans sync.WaitGroup
	//op_ch := make(chan *OpWire.Request_Operation, num_channels)
	//for i := 0; i < num_channels; i++ {
	//	wg_chans.Add(1)

	//	go func() {
	//		defer wg_chans.Done()
	//		for op := range op_ch {
	//			sleep_time := time.Until(start_time.Add(time.Duration(op.Start * float64(time.Second))))
	//			time.Sleep(sleep_time)
	//			perform(op, res_ch, cli, clientid, time.Now())
	//		}
	//	} ()
	//}

	res_ch := make(chan *OpWire.Response, 50000)
	done := make(chan bool)
	go result_loop(res_ch, out_writer, done)

	start_time := time.Now()
	var wg_perform sync.WaitGroup
	for _, op := range ops {
		wg_perform.Add(1)
		sleep_time := time.Until(start_time.Add(time.Duration(op.Start * float64(time.Second))))
		time.Sleep(sleep_time)
		//log.Print(op.Start, time.Now())
		go func () {
			defer wg_perform.Done()
			perform(op, res_ch, cli, clientid, time.Now())
		} ()
	}

	//close(op_ch)

	//Wait to complete ops
	wg_perform.Wait()

	//Signal end of results 
	close(res_ch)
	//Wait for results to be written
	<-done
}
