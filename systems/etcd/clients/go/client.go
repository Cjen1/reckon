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


func unix_seconds(t time.Time) float64 {
	return float64(t.UnixNano()) / 1e9
}

func put(cli *clientv3.Client, op *OpWire.Operation_Put, clientid uint32) *OpWire.Response {
	//println("CLIENT: Attempting to put")
	// TODO implement options
	st := op.Put.Start
	end := unix_seconds(time.Now())
	_, err := cli.Put(context.Background(), string(op.Put.Key), string(op.Put.Value))

	err_msg := "None"
	if(err != nil){
		err_msg = err.Error()
	}

	resp := &OpWire.Response {
		ResponseTime:		end-st,
		Err:			err_msg,
		Start:			st,
		End:			end,
		Clientid:		clientid,
		Optype:			true,
		Target:			cli.ActiveConnection().Target(),
	}

	//println("CLIENT: Successfully put")
	return resp
}

func get(cli *clientv3.Client, op *OpWire.Operation_Get, clientid uint32) *OpWire.Response {
	// TODO implement options
	//println("CLIENT: Attempting to get")
	st := op.Get.Start
	end := unix_seconds(time.Now())
	_, err := cli.Get(context.Background(), string(op.Get.Key))

	err_msg := "None"
	if(err != nil){
		err_msg = err.Error()
	}

	resp := &OpWire.Response {
		ResponseTime:		end-st,
		Err:			err_msg,
		Start:			st,
		End:			end,
		Clientid:		clientid,
		Optype:			false,
		Target:			cli.ActiveConnection().Target(),
	}

	//println("CLIENT:Successfully got")

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

func check(e error) {
	if e != nil {
		panic(e)
	}
}

func marshall_response(resp *OpWire.Response) string {
	payload, err := proto.Marshal(resp)
	check(err)
	return string(payload)
}

func main() {
	println("Starting client")

	endpoints := strings.Split(os.Args[1], ",")
	i, err := strconv.ParseUint(os.Args[2], 10, 32)
	check(err)
	address := os.Args[3]

	clientid := uint32(i)

	socket, _ := zmq.NewSocket(zmq.REQ)
	defer socket.Close()
	socket.Connect(address)

	for index, endpoint := range endpoints {
		endpoints[index] = endpoint + ":2379"
	}
	dialTimeout := 2 * time.Second

	cli, err := clientv3.New(clientv3.Config{
		DialTimeout:		dialTimeout,
		DialKeepAliveTime:	dialTimeout/2,
		DialKeepAliveTimeout:	dialTimeout*2,
		AutoSyncInterval:	dialTimeout/2,
		Endpoints:		endpoints,
	})
	defer cli.Close()
	check(err)

	//send ready signal
	socket.Send("",0)

	for {
		Operation := ReceiveOp(socket)

		switch op := Operation.OpType.(type) {
		case *OpWire.Operation_Put:
			resp := put(cli, op, clientid)
			payload := marshall_response(resp)
			socket.Send(payload, 0)

		case *OpWire.Operation_Get:
			resp := get(cli, op, clientid)
			payload := marshall_response(resp)
			socket.Send(payload, 0)

		case *OpWire.Operation_Quit:
			return

		default:
			resp := &OpWire.Response {
				ResponseTime:  -1,
				Err:			"Error: Operation was not found / supported",
				Start:			0,
				End:			0,
				Clientid:		clientid,
				Optype:			true,
			}
			payload := marshall_response(resp)
			socket.Send(payload, 0)
		}
	}
}
