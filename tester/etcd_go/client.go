package main

import (
	"log"
	"time"
	"context"
	"strings"
	"os"
	"strconv"

	zmq "github.com/pebbe/zmq4"
	"go.etcd.io/etcd/clientv3"
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

func put(cli *clientv3.Client, op *OpWire.Operation_Put, id uint32) *OpWire.Response {
	// TODO implement options
	st := time.Now()
	_, err := cli.Put(context.Background(), string(op.Put.Key), string(op.Put.Value))
	end := time.Now()
	duration := end.Sub(st)

	err_msg := "None"
	if(err != nil){
		err_msg = err.Error()
	}

	resp := &OpWire.Response {
		ResponseTime: 	duration.Seconds(),
		Err:			err_msg,
		Start: 			unix_seconds(st),  			
		End:			unix_seconds(end),
		Id: 			id,
	}

	return resp
}

func get(cli *clientv3.Client, op *OpWire.Operation_Get, id uint32) *OpWire.Response {
	// TODO implement options
	st := time.Now()
	_, err := cli.Get(context.Background(), string(op.Get.Key))
	end := time.Now()
	duration := end.Sub(st)

	err_msg := "None"
	if(err != nil){
		err_msg = err.Error()
	}

	resp := &OpWire.Response {
		ResponseTime: 	duration.Seconds(),
		Err:			err_msg,
		Start: 			unix_seconds(st),
		End:			unix_seconds(end),
		Id:				id,
	}

	return resp
}

func ReceiveOp(socket *zmq.Socket) *OpWire.Operation{
	//print("CLIENT: Awaiting Operation")
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
	if(len(os.Args) < 4){
		println("Incorrect number of arguments") }

	port := os.Args[1]
	endpoints := strings.Split(os.Args[2], ",")
	i, err := strconv.ParseUint(os.Args[3], 10, 32)
	if(err != nil){
		println(err)
		return
	}
	id := uint32(i)

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
			resp := put(cli, op, id)
			payload := marshall_response(resp) 
			socket.Send(payload, 0)

		case *OpWire.Operation_Get:
			resp := get(cli, op, id)
			payload := marshall_response(resp)
			socket.Send(payload, 0)

		case *OpWire.Operation_Quit:
			return

		default:
			resp := &OpWire.Response {
				ResponseTime:  -1,
				Err: 			"Error: Operation was not found / supported", 
				Start: 			0,
				End:			0,
				Id:				id,
			}
			payload := marshall_response(resp)
			socket.Send(payload, 0)
		}
	}
}
