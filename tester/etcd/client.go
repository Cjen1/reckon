package main

import (
	"log"
	"time"
	"context"

	"fmt"
	zmq "github.com/alecthomas/gozmq"

	"github.com/coreos/etcd/client"
	//TODO import protocol buffers
)

func receiveOp(context, port) {
	socket, _ := context.NewSocket(zmq.REP)
	defer socket.Close()

	socket.connect("127.0.0.1:" + port)

	msg, _ := socket.Recv(0)
	println("Received ", string(msg))

	op = &pb.Operation{}
	if err := proto.Unmarshal(msg, op); err != nil {
		log.Fatalln("Failed to parse incomming operation")
	}

	return op
}

func sendResp(context, port, msg) {
	socket, _ := context.NewSocket(zmq.REP)
	defer socket.Close()

	socket.Connect("127.0.0.1:" + port)

	socket.Send(msg, 0)
}

//func put(kapi, Op) {
//	// TODO implement options
//	st = time.Now()
//	resp, err := kapi.Set(context.Background(), Op.getKey(), Op.getVal(), nil)
//	duration = time.Since(st)
//
//	// TODO implement response_obj
//	return response_obj
//}
//
//func get(kapi, Op) {
//	// Todo implement options
//	st = time.Now()
//	resp, err := kapi.Get(context.Background(), Op.getKey(), nil)
//	duration = time.Since(st)
//
//	return response_obj
//}
//
//func setup(Op) {
//	cmd := exec.Command("/bin/sh", "etcd_start.sh")
//
//	cfg := client.Config{
//		Endpoints: 		Op.getEndpoints(),
//		Transport:		client.DefaultTransport,
//		HeaderTimeoutPerRequest: time.Second,
//	}
//
//	c, err := client.New(cfg)
//	if err != nil {
//		log.Fatal(err)
//	}
//
//	kapi := client.NewKeysAPI(c)
//
//	return response_obj, cfg, kapi
//}


func main() {
	context, _ := zmq.NewContext()
	defer context.Close()
	for {
		Op := receiveOp()

		switch x := Op.op_type.(type){
		default:
			fmt.Printf("%T", x)
			resp := &pb.Response {
				response_time: 	1,
				err : 			"this is now functional",
			}
			payload, err := proto.Marshal(resp)
			send(context, port, payload)
		}

//		var resp, cfg, kapi
//		switch Op.op_type.(type) {
//		case *Operation.setup:
//			resp, cfg, kapi = setup(Op, context)
//		case *Operation.put:
//			resp, _ := proto.Marshall(put(kapi, Op, context))
//			send(context, port, resp)
//		case *Operation.quit:
//			return
//		case nil:
//			fmt.println("Operation not set in incomming packet")
//		default:
//			resp = &pb.Response {
//				response_time:  -1,
//				err:	 		fmt.Errorf("Operation.op_type is unrecongnised: %T", x)
//			}
//			
//			payload, err := proto.Marshal(resp)
//			if err != nil {
//				log.Fatalln("Failed to encode response")
//			}
//
//			send(context, port, payload)
//
//			return resp.err
//		}
	}
}
	
