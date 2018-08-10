package main

import (
	"log"
	"time"
	"strings"
	"os"
	"fmt"

	zmq "github.com/pebbe/zmq4"
	"github.com/hashicorp/consul/api"
	"github.com/golang/protobuf/proto"
	"./OpWire"
)

var (
	dialTimeout = 2 * time.Second
	requestTimeout = 10 * time.Second
)


func put(cli *api.Client, op *OpWire.Operation_Put) *OpWire.Response {
	kv := cli.KV()
	p := &api.KVPair{Key: fmt.Sprintf("%v", op.Put.Key), Value: []byte(string(op.Put.Value))}
	st := time.Now()
	_, err := kv.Put(p, nil)
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

func get(cli *api.Client, op *OpWire.Operation_Get) *OpWire.Response {
	kv := cli.KV()

	st := time.Now()
	_, _, err := kv.Get(fmt.Sprintf("%v",op.Get.Key), nil)
	duration := time.Since(st)
	var resp *OpWire.Response
	if(err != nil) {
		resp = &OpWire.Response {
			ResponseTime: 	duration.Seconds(),
			Err: 			err.Error(),
		}
	} else /* if p!= nil */ {
		resp = &OpWire.Response {
			ResponseTime: 	duration.Seconds(),
			Err: 			"None",	
		}
		fmt.Println("Great Success")
	}/*  else {
		resp = &OpWire.Response {
			ResponseTime: duration.Seconds(),
			Err: fmt.Sprintf("Key-Value Pair not found... (Key %v)", op.Get.Key),
		}
	}*/

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

func ReceiveOp(socket *zmq.Socket) *OpWire.Operation{
	fmt.Println("Test1")
	payload, _ := socket.Recv(0)
	fmt.Println("Test2")
	op := &OpWire.Operation{}

	if err := proto.Unmarshal([]byte(payload), op); err != nil {
		log.Fatalln("Failed to parse incomming operation")
	}

	return op
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

	cli, err := api.NewClient(&api.Config{
				Address:endpoints[0] + ":8500",
		        })

	if(err != nil){
		println(err)
		return
	}

	binding := "tcp://127.0.0.1:" + port
	socket.Bind(binding)

	for {

		Operation := ReceiveOp(socket)

		switch op := Operation.OpType.(type) {
		case *OpWire.Operation_Put:
			resp := put(cli, op)
			payload := marshall_response(resp) 
			socket.Send(payload, 0)
/*
		case *OpWire.Operation_Get:
			resp := get(cli, op)
			payload := marshall_response(resp) 
			socket.Send(payload, 0)
*/
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
