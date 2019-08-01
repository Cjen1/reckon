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

func check(e error) {
	if e != nil {
		panic(e)
	}
}

func main() {

	endpoints := strings.Split(os.Args[1], ",")
	i, err := strconv.ParseUint(os.Args[2], 10, 32)
	check(err)
	address := os.Args[3]

	clientid := uint32(i)

	for index, endpoint := range endpoints {
		endpoints[index] = endpoint + ":2379"
	}

	socket, _ := zmq.NewSocket(zmq.REQ)
	defer socket.Close()
	socket.Connect(address)

	socket.Send("", 0)

	for {
		Operation := ReceiveOp(socket)

		switch Operation.OpType.(type) {
		case *OpWire.Operation_Put:
			resp := &OpWire.Response {
				ResponseTime:	1,
				Clientid:	clientid,
			}
			payload := marshall_response(resp)
			socket.Send(payload, 0)

		case *OpWire.Operation_Get:
			resp := &OpWire.Response {
				ResponseTime:   2,
				Clientid:	clientid,
			}
			payload := marshall_response(resp)
			socket.Send(payload, 0)

		case *OpWire.Operation_Quit:
			return

		default:
			resp := &OpWire.Response {
				ResponseTime:  -1,
				Err:			"Error: Operation was not found / supported",
				Clientid:		clientid,
			}
			payload := marshall_response(resp)
			socket.Send(payload, 0)
		}
	}
}
