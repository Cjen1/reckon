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

func unix_seconds(t time.Time) float64 {
	return float64(t.UnixNano()) / 1e9
}

func put(cli *clientv3.Client, op *OpWire.Operation_Put) *OpWire.Response {
	// TODO implement options
	st := time.Now()
	_, err := cli.Put(context.Background(), string(op.Put.Key), string(op.Put.Value))
	end := time.Now()
	duration := end.Sub(st)

	err_msg := ""
	if(err != nil){
		err_msg = err.Error()
	}

	resp := &OpWire.Response {
		ResponseTime: 	duration.Seconds(),
		Err:			err_msg,
		St: 			unix_seconds(st),  			
		End:			unix_seconds(end),
	}

	return resp
}

func get(cli *clientv3.Client, op *OpWire.Operation_Get) *OpWire.Response {
	// TODO implement options
	st := time.Now()
	_, err := cli.Get(context.Background(), string(op.Get.Key))
	end := time.Now()
	duration := end.Sub(st)

	err_msg := ""
	if(err != nil){
		err_msg = err.Error()
	}

	resp := &OpWire.Response {
		ResponseTime: 	duration.Seconds(),
		Err:			err_msg,
		St: 			unix_seconds(st),  			
		End:			unix_seconds(end),
	}

	return resp
}

func ReceiveOp(socket *zmq.Socket) *OpWire.Operation{
	payload, _ := socket.Recv(0)
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
	if(len(os.Args) < 3){
		println("Incorrect number of arguments") }

	port := os.Args[1]
	endpoints := strings.Split(os.Args[2], ",")
	for index, endpoint := range endpoints {
		endpoints[index] = endpoint + ":2379"
	}

	cli, err := clientv3.New(clientv3.Config{
		DialTimeout: 	dialTimeout,
		Endpoints: 		endpoints,
	})
 	defer cli.Close()

	if(err != nil){
		println(err)
		return
	}

	socket, _ := zmq.NewSocket(zmq.REQ)
	defer socket.Close() 

	//println("Sending ready signal")
	//print(port)

	binding := "tcp://127.0.0.1:" + port 
	socket.Connect(binding)
	socket.Send("",0)

	//send ready signal
	for {
		Operation := ReceiveOp(socket)

		switch op := Operation.OpType.(type) {
		case *OpWire.Operation_Put:
			resp := put(cli, op)
			payload := marshall_response(resp) 
			socket.Send(payload, 0)

		case *OpWire.Operation_Get:
			resp := get(cli, op)
			payload := marshall_response(resp)
			socket.Send(payload, 0)

		case *OpWire.Operation_Quit:
			return

		default:
			resp := &OpWire.Response {
				ResponseTime:  -1,
				Err: 			"Error: Operation was not found / supported", 
			}
			payload := marshall_response(resp)
			socket.Send(payload, 0)
		}
	}
}
