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
	"encoding/hex"
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
	_, err := cli.Put(context.Background(), string(op.Put.Key), string(op.Put.Value))
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

func perform(op *OpWire.Request_Operation, res_ch chan *OpWire.Response, cli *clientv3.Client, clientid uint32, wg sync.WaitGroup) {
	start := op.Start
	switch op_t := op.OpType.(type) {
	case *OpWire.Request_Operation_Put:
		put(res_ch, cli, op_t, clientid, start)
	case *OpWire.Request_Operation_Get:
		get(res_ch, cli, op_t, clientid, start)
	default:
		resp := &OpWire.Response{
			ResponseTime: -1,
			Err:          fmt.Sprintf("Error: Operation (%v) was not found / supported", op),
			Clientid:     clientid,
			Optype:       "Error",
		}
		res_ch <- resp
	}
	wg.Done()
}

func recv(reader *bufio.Reader) *OpWire.Request{
	log.Print("Trying to read len")
	var size uint32
	if err := binary.Read(reader, binary.LittleEndian, &size); err != nil {
		log.Fatal(err)
	}

	log.Printf("received size = %d\n", size)

	payload := make([]byte, size)
	if _, err := io.ReadFull(reader, payload); err != nil {
		log.Fatal(err)
	}
	log.Printf("-------\nreceived payload = %s\n-------", (hex.EncodeToString(payload)))

	op := &OpWire.Request{}
	if err := proto.Unmarshal([]byte(payload), op); err != nil {
		log.Fatal("Failed to parse incomming operation")
	}
	return op
}

func recv_loop(quit_ch chan interface{}, res_ch chan *OpWire.Response, cli *clientv3.Client, clientid uint32){
}

func marshall_response(resp *OpWire.Response) []byte {
	payload, err := proto.Marshal(resp)
	check(err)
	return payload
}

func send(writer *bufio.Writer, msg []byte){
	var size uint32
	size = uint32(len(msg))
	log.Printf("send size = %L", size)
	size_part := make([]byte, 4)
	binary.LittleEndian.PutUint32(size_part, size)

	payload := append(size_part[:], msg[:]...)
	_, err := writer.Write(payload)
	check(err)

	writer.Flush()
}

func init() {
	log.SetOutput(os.Stderr)
	log.SetFlags(log.Ltime | log.Lmicroseconds)
}

func result_loop(res_ch chan *OpWire.Response, out *bufio.Writer, done chan bool) {
	for res := range res_ch {
		payload := marshall_response(res)
		send(out, payload)
	}
	done <- true
}

func main() {
	log.Print("Client: Starting client")

	endpoints := strings.Split(os.Args[1], ",")
	log.Printf("%v\n", endpoints)

	i, err := strconv.ParseUint(os.Args[2], 10, 32)
	check(err)

	clientid := uint32(i)

	log.Printf("Client: creating file")
	result_pipe := os.Args[3]
	log.Print(result_pipe)
	file, err := os.OpenFile(result_pipe, os.O_WRONLY, 0755)
	check(err)
	defer file.Close()

	out_writer := bufio.NewWriter(file)

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

	res_ch := make(chan *OpWire.Response, 5000)

	reader := bufio.NewReader(os.Stdin)

	//Phase 1: preload
	log.Print("Phase 1: preload")
	prereq_ch := make(chan *OpWire.Response)
	prereqs_dispatched := 0
	var ops []*OpWire.Request_Operation
	var wg_null sync.WaitGroup //ignore this
	for {
		op := recv(reader)

		switch op.Kind.(type) {
		case *OpWire.Request_Op:
			if op.GetOp().Prereq {
				perform(op.GetOp(), prereq_ch, cli, clientid, wg_null)
				prereqs_dispatched ++
			} else {
				ops = append(ops, op.GetOp())
			}
		case *OpWire.Request_Finalise_:
			break
		default:
			log.Fatal("Got unrecognised message...")
		}
	}

	//Phase 2: Readying
	log.Print("Phase 2: Readying")
	for received := 0; received < prereqs_dispatched; received++ {
		<-prereq_ch
	}
	send(out_writer, []byte(""))

	//Phase 3: Execute
	log.Print("Phase 3: Execute")
	var start_time time.Time
	for {
		op := recv(reader)
		switch op.Kind.(type) {
		case *OpWire.Request_Start_:
			start_time = time.Now()
			break
		default:
			log.Fatal("Got a message which wasn't a start!")
		}
	}

	done := make(chan bool)
	go result_loop(res_ch, out_writer, done)

	var wg_perform sync.WaitGroup
	for _, op := range ops {
		time.Sleep(time.Until(start_time.Add(time.Duration(op.Start * float64(time.Second)))))
		wg_perform.Add(1)
		go perform(op, res_ch, cli, clientid, wg_perform)
	}

	//Wait to complete ops
	wg_perform.Wait()

	//Signal end of results 
	close(res_ch)
	//Wait for results to be written
	<-done
}
