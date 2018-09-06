package main

import (
	"log"
	"time"
	"strings"
	"os"
	"os/exec"
	"fmt"
	"strconv"

	zmq "github.com/pebbe/zmq4"
	"github.com/hashicorp/consul/api"
	"github.com/golang/protobuf/proto"
	"./OpWire"
)

var (
	dialTimeout = 2 * time.Second
	requestTimeout = 10 * time.Second
)


func put(cli *api.Client, op *OpWire.Operation_Put, id uint32) *OpWire.Response {
	kv := cli.KV()
	p := &api.KVPair{Key: fmt.Sprintf("%v", op.Put.Key), Value: []byte(string(op.Put.Value))}
	st := time.Now()
	_, err := kv.Put(p, nil)
	end := time.Now()
	duration := end.Sub(st)

	var resp *OpWire.Response
	if(err != nil) {
		resp = &OpWire.Response {
			ResponseTime:	duration.Seconds(),
			Err:		err.Error(),
			Start:		float64(st.UnixNano())/1e9,
			End:		float64(end.UnixNano())/1e9,
			Id:		id,
		}
	} else {
		resp = &OpWire.Response {
			ResponseTime: 	duration.Seconds(),
			Err: 			"None",
			Start:		float64(st.UnixNano())/1e9,
			End:		float64(end.UnixNano())/1e9,
			Id:		id,
		}
	}

	return resp
}

func get(cli *api.Client, op *OpWire.Operation_Get, id uint32) *OpWire.Response {
	kv := cli.KV()

	st := time.Now()
	p, _, err := kv.Get(fmt.Sprintf("%v",op.Get.Key), nil)
	end := time.Now()
	duration := end.Sub(st)
	var resp *OpWire.Response
	if(err != nil) {
		resp = &OpWire.Response {
			ResponseTime: 	duration.Seconds(),
			Err: 			err.Error(),
			Start:		float64(st.UnixNano()) / 1e9,
			End:		float64(end.UnixNano()) / 1e9,
			Id: 		id,
		}
	} else if p!= nil  {
		resp = &OpWire.Response {
			ResponseTime: 	duration.Seconds(),
			Err: 		"None",
			Start:		float64(st.UnixNano()) / 1e9,
			End:		float64(end.UnixNano()) / 1e9,
			Id: 		id,
		}
	} else{
		resp = &OpWire.Response {
			ResponseTime: duration.Seconds(),
			Err: fmt.Sprintf("Key-Value Pair not found... (Key %v)", op.Get.Key),
			Start:		float64(st.UnixNano()) / 1e9,
			End:		float64(end.UnixNano()) / 1e9,
			Id:		id,
		}
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
	port := os.Args[1]
	endpoints := strings.Split(os.Args[2], ",")

	tmpid, _ := strconv.Atoi(os.Args[3])
	clientid := uint32(tmpid)

	socket, _ := zmq.NewSocket(zmq.REQ)
	defer socket.Close()

	client_agent = Command(
		"consul", "agent",
		"-bind", "0.0.0.0:" + strconv(60000 + clientid),
		"-disable-host-node-id",
		"-retry-join", endpoints[0],
	)

	consulconfig = api.DefaultConfig()
	consulconfig.Address = endpoints[0] + ":8500"

	cli, err := api.NewClient(consulconfig)

	if(err != nil){
		println(err)
		return
	}

	binding := "tcp://127.0.0.1:" + port
	socket.Connect(binding)
	socket.Send("", 0)
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
				ResponseTime:  -10000.0,
				Err:			"Error: Operation was not found / supported", 
				Start:		0.0,
				End:		0.0,
				Id:		clientid,
			}
			payload := marshall_response(resp)
			socket.Send(payload, 0)
			break
		}
	}
}
