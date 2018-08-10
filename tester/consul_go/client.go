package main

import (
//        "log"
//        "time"
        "strings"
        "os"
        "fmt"

//        zmq "github.com/pebbe/zmq4"
//        "github.com/hashicorp/consul/api"
//        "github.com/golang/protobuf/proto"
//        "./OpWire"
)
/*
func put(cli *api.Client, op *OpWire.Operation_Put) *OpWire.Response {
	return nil
}

func get(cli *api.Client, op *OpWire.Operation_Get) *OpWire.Response {
	return nil
}

func quit(op *OpWire.Operation_Quit, socket *zmq.Socket) {
        resp := &OpWire.Response {
	                ResponseTime:   0,
	                Err:                    "Endpoint Quitting",
	}
	payload := marshall_response(resp)
        socket.Send(payload, 0)
	return
}

func ReceiveOp(socket *zmq.Socket)  *OpWire.Operation{
	return nil
}

func marshall_response(resp *OpWire.Response) string {
        payload, err := proto.Marshal(resp)
        if err != nil {
                log.Fatalln("Failed to encode response: " + err.Error())
        }
        return string(payload)
}
*/
func main(){

	port := os.Args[1]
	endpoints := strings.Split(os.Args[2], ",")
	fmt.Println(port)
	fmt.Println(endpoints)
}
