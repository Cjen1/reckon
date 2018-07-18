package main

import (
	"log"
	"time"
	"context"
	"strings"
	"os"

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
	//port := *flag.String("port", "4444", "Local port to use for input")
	//endpoints := strings.Split(*flag.String("endpoints", "NONE", "Endpoints for client to use, comma delimited. Format: https://<ip>:<client port>"), ",")

	port := os.Args[1]
	endpoints := strings.Split(os.Args[2], ",")

	socket, _ := zmq.NewSocket(zmq.REP)
	defer socket.Close()
	
	cli, err := clientv3.New(clientv3.Config{
		DialTimeout: 	dialTimeout,
		Endpoints: 		endpoints,
	})
 	defer cli.Close()

	if(err != nil){
		println(err)
		return
	}

	for {
		binding := "tcp://127.0.0.1:" + port

		socket.Bind(binding)

		Operation := ReceiveOp(socket)

		switch op := Operation.OpType.(type) {
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
