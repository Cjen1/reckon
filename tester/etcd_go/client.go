package main

import (
	"log"
	"time"
	"context"
	"os/exec"
	"strings"
	"fmt"

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
	// TODO implement options
	st := time.Now()
	_, err := cli.Put(context.Background(), string(op.Put.Key), string(op.Put.Value))
	duration := time.Since(st)

	var resp *OpWire.Response
	if(err != nil) {
		resp = &OpWire.Response {
			ResponseTime: 	duration.Seconds(),
			Err: 			err.Error(),
		}
	} else {
		resp = &OpWire.Response {
			ResponseTime: 	duration.Seconds(),
			Err: 			"None",	
		}
	}

	return resp
}

func get(cli clientv3.Client, op *OpWire.Operation_Get) *OpWire.Response {
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
	// get remote servers running
	//TODO generalise setup to support multiple numbers of hosts
	stdout, err := exec.Command("./etcd_go/etcd_start.sh", strings.Join(op.Setup.Hostnames, " ")).Output()

	if(err != nil) {
		fmt.Println("Err:", err)
		fmt.Println("Stdout:", stdout)
		fmt.Println("Endpoints:", op.Setup.Endpoints)
		fmt.Println("Hostnames:", op.Setup.Hostnames)
	}

	endpoints := make([]string, len(op.Setup.Endpoints))
	for i := 0; i < len(op.Setup.Endpoints); i++ {
		endpoints[i] = "http://" + op.Setup.Endpoints[i] + ":2379"
	}

	cli, _ := clientv3.New(clientv3.Config{
		DialTimeout: 	dialTimeout,
		Endpoints: 		endpoints,
	})

	return cli
}

func quit(op *OpWire.Operation_Quit, socket *zmq.Socket) {
	resp := &OpWire.Response {
		ResponseTime:	0,
		Err:			"Endpoint Quitting",
	}
	payload := marshall_response(resp)
	socket.Send(payload, 0)
	return
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
	defer cli.Close()

	for {
		binding := "tcp://127.0.0.1:" + port

		socket.Bind(binding)

		Operation := ReceiveOp(socket)

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
			quit(op, socket)
			break

		default:
			resp := &OpWire.Response {
				ResponseTime:  0,
				Err: 			"Error: Operation was not found / supported", 
			}
			payload := marshall_response(resp)
			socket.Send(payload, 0)
			break	
		}
	}
}
