package main

import (
	"bufio"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"log"
	"math/rand"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"client/OpWire"
	"client/PaxWire"
	"github.com/golang/protobuf/proto"
	zmq "github.com/pebbe/zmq4"
)

func unix_seconds(t time.Time) float64 {
	return float64(t.UnixNano()) / 1e9
}

func check(e error) {
	if e != nil {
		log.Fatal(e)
	}
}

type ch_payload struct {
	rid string
	msg string
}

type OP_client struct {
	endpoints map[string]chan ch_payload
	cid       int32
	context   *zmq.Context
	in_flight *sync.Map //map[string]chan *PaxWire.Response
}

type PutResponse struct{}

func (cli OP_client) Put(key string, value string) (*PutResponse, error) {
	rid := fmt.Sprint(rand.Int31())

	res_ch := make(chan *PaxWire.Response)
	cli.in_flight.Store(rid, res_ch)

	msg := &PaxWire.Request{
		Type:  PaxWire.Request_WRITE,
		Id:    rand.Int31(),
		Key:   key,
		Value: value,
	}

	payload, err := proto.Marshal(msg)
	check(err)

	log.Printf("Sending request for rid: <%s>", rid)

	for _, ch := range cli.endpoints {
		ch <- ch_payload{
			rid: rid,
			msg: string(payload),
		}
	}

	res := <-res_ch
	log.Printf("Got result for rid: <%s>", rid)
	switch res.Result {
	case PaxWire.Response_WRITESUCCESS:
		return &PutResponse{}, nil
	case PaxWire.Response_READSUCCESS:
		return nil, errors.New("Got read response for write")
	default:
		return nil, errors.New("Returned Failure")
	}
}

type GetResponse struct{}

func (cli OP_client) Get(key string) (*GetResponse, error) {
	rid := string(rand.Int31())

	res_ch := make(chan *PaxWire.Response)
	cli.in_flight.Store(rid, res_ch)

	msg := &PaxWire.Request{
		Type:  PaxWire.Request_READ,
		Id:    rand.Int31(),
		Key:   key,
		Value: "",
	}

	payload, err := proto.Marshal(msg)
	check(err)

	for _, ch := range cli.endpoints {
		ch <- ch_payload{
			rid: rid,
			msg: string(payload),
		}
	}

	res := <-res_ch
	switch res.Result {
	case PaxWire.Response_WRITESUCCESS:
		return nil, errors.New("Got write response for read")
	case PaxWire.Response_READSUCCESS:
		return &GetResponse{}, nil
	default:
		return nil, errors.New("Returned Failure")
	}
}

type loop_state struct {
	socket_in  *zmq.Socket
	socket_out *zmq.Socket
	dealer     *zmq.Socket
	in_channel *chan ch_payload
	in_flight  *sync.Map
	endpoint string
}

func (s loop_state) link_out_dealer(state zmq.State) error {
	log.Print("Got socket_out msg")
	rid, err := s.socket_out.Recv(0)
	check(err)
	msg, err := s.socket_out.Recv(0)
	check(err)
	_, err = s.dealer.Send(rid, zmq.SNDMORE)
	check(err)
	_, err = s.dealer.Send(msg, 0)
	check(err)
	log.Print("Forwarded msg from socket_out and sent to dealer %s", s.endpoint)
	return err
}

func (s loop_state) link_ch_in() {
	for payload := range *s.in_channel {
		_, err := s.socket_in.Send(payload.rid, zmq.SNDMORE)
		check(err)
		_, err = s.socket_in.Send(payload.msg, 0)
		check(err)
	}
	log.Printf("Exiting link_ch_in for endpoint: %s", s.endpoint)
}

func (s loop_state) recv_loop(state zmq.State) error {
	log.Print("Got response")
	rid, err := s.dealer.Recv(0)
	check(err)
	payload, err := s.dealer.RecvBytes(0)
	check(err)
	ch, ok := s.in_flight.Load(rid)
	if ok {
		msg := &PaxWire.Response{}
		err = proto.Unmarshal(payload, msg)
		check(err)
		(ch.(chan *PaxWire.Response)) <- msg
	}
	return err
}

func create(endpoints_strings []string) *OP_client {
	ctx, err := zmq.NewContext()
	check(err)

	reactor := zmq.NewReactor()
	var in_flight sync.Map
	//in_flight := make(map[string]chan *PaxWire.Response)

	endpoints := make(map[string]chan ch_payload)
	for _, endpoint := range endpoints_strings {
		addr := "inproc://" + endpoint
		socket_in, err := ctx.NewSocket(zmq.PAIR)
		check(err)
		socket_in.Bind(addr)

		socket_out, err := ctx.NewSocket(zmq.PAIR)
		check(err)
		socket_out.Connect(addr)

		dealer, err := ctx.NewSocket(zmq.DEALER)
		dealer.SetIdentity("test")
		check(err)
		dealer.Connect("tcp://" + endpoint)

		in_channel := make(chan ch_payload)
		endpoints[endpoint] = in_channel

		log.Print("Set up sockets and channels")

		state := loop_state{
			socket_in:socket_in,
			socket_out:socket_out,
			dealer:dealer,
			in_channel:&in_channel,
			in_flight:&in_flight,
			endpoint:endpoint,
		}

		reactor.AddSocket(socket_out, zmq.POLLIN, state.link_out_dealer)
		go state.link_ch_in()
		reactor.AddSocket(dealer, zmq.POLLIN, state.recv_loop)
	}

	log.Print("Added sockets, starting reactor")
	go reactor.Run(-1)

	cli := OP_client{
		endpoints: endpoints,
		cid:       rand.Int31(),
		context:   ctx,
		in_flight: &in_flight,
	}
	log.Print("returning from function")
	return &cli
}

func put(res_ch chan *OpWire.Response, cli *OP_client, op *OpWire.Request_Operation_Put, clientid uint32, start float64) {
	// TODO implement options
	st := unix_seconds(time.Now())
	var err error
	if true {
		_, err = cli.Put(string(op.Put.Key), string(op.Put.Value))
	}
	end := unix_seconds(time.Now())

	err_msg := "None"
	if err != nil {
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
		Target:       "",
	}

	//log.Print("CLIENT: Successfully put")

	res_ch <- resp
}

func get(res_ch chan *OpWire.Response, cli *OP_client, op *OpWire.Request_Operation_Get, clientid uint32, start float64) {
	st := unix_seconds(time.Now())
	_, err := cli.Get(string(op.Get.Key))
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
		Target:       "",
	}

	//log.Print("CLIENT:Successfully got")

	res_ch <- resp
}

func perform(op *OpWire.Request_Operation, res_ch chan *OpWire.Response, cli *OP_client, clientid uint32, start_time time.Time) {
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

func recv(reader *bufio.Reader) *OpWire.Request {
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

func send(writer *os.File, msg []byte) {
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
	for range res_ch {
	}
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
	out_writer := file

	log.Print("creating client")
	cli := create(endpoints)

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
			log.Print("Got unrecognised message...")
			log.Print(op)
			log.Fatal("Quitting due to unrecognised message")
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
	for !got_start {
		op := recv(reader)
		switch op.Kind.(type) {
		case *OpWire.Request_Start_:
			log.Print("Got start_request")
			got_start = true
		default:
			log.Fatal("Got a message which wasn't a start!")
		}
	}

	res_ch := make(chan *OpWire.Response, 50000)
	done := make(chan bool)
	go result_loop(res_ch, out_writer, done)

	//channels := 1000
	//conns := make([]* chan OpWire.Request_Operation, channels)

	//var wg_perform sync.WaitGroup
	//for ch := range conns {
	//	wg_perform.Add(1)
	//	go func() {
	//		defer wg_perform.Done()
	//		for op := range ch {
	//			perform(op, res_ch, cli, clientid, t)
	//		}
	//	} ()
	//}

	//start_time := time.Now()
	//for i, op := range ops {
	//	end_time := start_time.Add(time.Duration(op.Start * float64(time.Second)))
	//	for t := time.Now() ; t < end_time; {}
	//	conns[i % channels] <- op
	//}

	start_time := time.Now()
	var wg_perform sync.WaitGroup
	for _, op := range ops {
		//log.Print("Attempting to perform")
		wg_perform.Add(1)
		end_time := start_time.Add(time.Duration(op.Start * float64(time.Second)))
		//log.Print(end_time)
		t := time.Now()
		for ; t.Before(end_time); t = time.Now() {
		}
		//log.Print("At right time")
		go func() {
			defer wg_perform.Done()
			perform(op, res_ch, cli, clientid, t)
		}()
	}

	//Wait to complete ops
	wg_perform.Wait()

	//Signal end of results
	close(res_ch)
	//Wait for results to be written
	<-done
}
