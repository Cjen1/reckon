package main

import (
	"log"
	"time"
	//"strings"
	"os"
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
	//endpoints := strings.Split(os.Args[2], ",")

	tmpid, _ := strconv.Atoi(os.Args[3])
	clientid := uint32(tmpid)

	socket, _ := zmq.NewSocket(zmq.REQ)
	defer socket.Close()

	// ca_port_http := strconv.FormatUint(uint64(60000 + clientid * 4), 10)
	// ca_port_lan  := strconv.FormatUint(uint64(60000 + clientid * 4 + 1), 10)
	// ca_port_wan  := strconv.FormatUint(uint64(60000 + clientid * 4 + 2), 10)
	// ca_port_dns  := strconv.FormatUint(uint64(60000 + clientid * 4 + 3), 10)

	// conn, err := net.Dial("udp", "8.8.8.8:80")
	// defer conn.Close()
	// localAddr := conn.LocalAddr().(*net.UDPAddr)

	// client_agent := exec.Command(
	// 	"consul", "agent",
	// 	"-disable-host-node-id", "-name=np"+ca_port_http,
	// 	"-retry-join="+endpoints[0],
	// 	"-advertise="+localAddr,
	// 	"-data-dir=~/consul_data"+ca_port_http,
	// 	"-http-port="+ca_port_http,
	// 	"-serf-lan-port="+ca_port_lan,
	// 	"-serf-wan-port="+ca_port_wan,
	// 	"-dns-port="+ca_port_dns,
	// )

	// client_agent.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
	// client_agent.Start()
	// defer syscall.Kill(-client_agent.Process.Pid, syscall.SIGKILL)

	consulconfig := api.DefaultConfig()
	consulconfig.Address = "127.0.0.1:8500"

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
