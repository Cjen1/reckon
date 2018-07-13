package main

import (
	"log"
	"time"
	"context"
	"os/exec"
	"strings"

	zmq "github.com/pebbe/zmq4"
	"github.com/coreos/etcd/clientv3"
	"github.com/golang/protobuf/proto"
	"./OpWire"
)

var (
	dialTimeout = 2 * time.Second
	requestTimeout = 10 * time.Second
)

func ReceiveOp(socket *zmq.Socket) *OpWire.Operation{
	payload, _ := socket.Recv(0)

	op := &OpWire.Operation{}

	if err := proto.Unmarshal([]byte(payload), op); err != nil {
		log.Fatalln("Failed to parse incomming operation")
	}

	return op
}

func put(cli *clientv3.Client, op *OpWire.Operation_Put) *OpWire.Response {
	println("Put Op")
	// TODO implement options
	st := time.Now()
	_, err := cli.Put(context.Background(), string(op.Put.Key), string(op.Put.Value))
	duration := time.Since(st)

	resp := &OpWire.Response {
		ResponseTime: 	duration.Seconds(),
		Err: 			err.Error(),
	}

	return resp
}

func get(cli clientv3.Client, op *OpWire.Operation_Get) *OpWire.Response {
	println("Get Op")
	// Todo implement options
	st := time.Now()
	_, err := cli.Get(context.Background(), string(op.Get.Key))
	duration := time.Since(st)

	resp := &OpWire.Response {
		ResponseTime: 	duration.Seconds(),
		Err:			err.Error(),
	}

	return resp
}

func setup(op *OpWire.Operation_Setup) *clientv3.Client{
	println("Setup Op")
	// get remote servers running
	cmd := exec.Command("/bin/sh", "etcd_start.sh", strings.Join(op.Setup.Endpoints, " "))
	stdout, err := cmd.Output()
	println(string(stdout))
	if(err != nil) {
		println(err.Error())
	}

	cli, _ := clientv3.New(clientv3.Config{
		DialTimeout: 	dialTimeout,
		Endpoints: 		op.Setup.Endpoints,
	})

	return cli
}

func marshall_response(resp *OpWire.Response) string {
	payload, err := proto.Marshal(resp)
	if err != nil {
		log.Fatalln("Failed to encode response: " + err.Error()) 
	}

	return string(payload)
}
	

func main() {
	port := "4444"
	socket, _ := zmq.NewSocket(zmq.REP)
	defer socket.Close()
	
	var cli *clientv3.Client

	println(requestTimeout)
	defer cli.Close()

	for {
		binding := "tcp://127.0.0.1:" + port

		socket.Bind(binding)

		println("Awaiting operation on " + binding)
		Operation := ReceiveOp(socket)

		println("Got operation")

		switch op := Operation.OpType.(type) {
		case *OpWire.Operation_Setup:
			cli = setup(op)
			resp := &OpWire.Response {
				ResponseTime: 	0,
				Err:			"Client set up correctly",
			}
			payload := marshall_response(resp)
			socket.Send(payload,0)

		case *OpWire.Operation_Put:
			resp := put(cli, op)
			payload := marshall_response(resp) 
			socket.Send(payload, 0)

		case *OpWire.Operation_Quit:
			resp := &OpWire.Response {
				ResponseTime:	0,
				Err:			"Endpoint Quitting",
			}
			payload := marshall_response(resp)
			socket.Send(payload, 0)
			return

		default:
			resp := &OpWire.Response {
				ResponseTime:  0,
				Err: 			"Error: Operation was not found / supported", 
			}
			payload := marshall_response(resp)
			socket.Send(payload, 0)
			return
		}
	}
}
	
