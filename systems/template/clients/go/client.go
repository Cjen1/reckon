package main

import (
	"log"
	"time"
	"strings"
	"os"
	"strconv"

	zmq "github.com/pebbe/zmq4"
	"github.com/golang/protobuf/proto"
	"./OpWire"
)


func unix_seconds(t time.Time) float64 {
	return float64(t.UnixNano()) / 1e9
}

func put(op *OpWire.Operation_Put, clientid uint32) *OpWire.Response {
	//println("CLIENT: Attempting to put")
	// TODO implement options
	st := op.Put.Start
	//_, err := cli.Put(context.Background(), string(op.Put.Key), string(op.Put.Value))
	end := unix_seconds(time.Now())

	err_msg := "None"
	//if(err != nil){
	//	err_msg = err.Error()
	//}

	resp := &OpWire.Response {
		ResponseTime:		end-st,
		Err:			err_msg,
		Start:			st,
		End:			end,
		Clientid:		clientid,
		Opid:			op.Put.Opid,
	}

	//println("CLIENT: Successfully put")
	return resp
}

func get(op *OpWire.Operation_Get, clientid uint32) *OpWire.Response {
	// TODO implement options
	//println("CLIENT: Attempting to get")
	st := op.Get.Start
	//_, err := cli.Get(context.Background(), string(op.Get.Key))
	end := unix_seconds(time.Now())

	err_msg := "None"
	//if(err != nil){
	//	err_msg = err.Error()
	//}

	resp := &OpWire.Response {
		ResponseTime:		end-st,
		Err:			err_msg,
		Start:			st,
		End:			end,
		Clientid:		clientid,
		Opid:			op.Get.Opid,
	}

	//println("CLIENT:Successfully got")

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
	println("Starting client") 
	if(len(os.Args) < 4){
		println("Incorrect number of arguments") }

	port := os.Args[1]
	endpoints := strings.Split(os.Args[2], ",")
	i, err := strconv.ParseUint(os.Args[3], 10, 32)
	if(err != nil){
		println(err)
		return
	}
	clientid := uint32(i)

	for index, endpoint := range endpoints {
		endpoints[index] = endpoint + ":2379"
	}

	socket, _ := zmq.NewSocket(zmq.REQ)
	defer socket.Close()

	//println("Sending ready signal")
	//print(port)

	println("sending ready signals")
	binding := "tcp://127.0.0.1:" + port
	socket.Connect(binding)
	socket.Send("",0)

	//send ready signal
	for {
		Operation := ReceiveOp(socket)

		switch op := Operation.OpType.(type) {
		case *OpWire.Operation_Put:
			resp := put(op, clientid)
			payload := marshall_response(resp)
			socket.Send(payload, 0)

		case *OpWire.Operation_Get:
			resp := get(op, clientid)
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
				Opid:			0,
			}
			payload := marshall_response(resp)
			socket.Send(payload, 0)
		}
	}
}
