package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"
	"time"
	"bufio"
	"io"
	"encoding/binary"
	"encoding/hex"

	"client/OpWire"
	"github.com/golang/protobuf/proto"
	zmq "github.com/pebbe/zmq4"
	"go.etcd.io/etcd/clientv3"
)

func unix_seconds(t time.Time) float64 {
	return float64(t.UnixNano()) / 1e9
}

func put(res_ch chan *OpWire.Response, cli *clientv3.Client, op *OpWire.Operation_Put, clientid uint32) {
	// TODO implement options
	st := unix_seconds(time.Now())
	_, err := cli.Put(context.Background(), string(op.Put.Key), string(op.Put.Value))
	end := unix_seconds(time.Now())

	err_msg := "None"
	if err != nil {
		err_msg = "ERROR WAS FOUND: " + err.Error()
	}

	resp := &OpWire.Response{
		ResponseTime: end - op.Put.Start,
		Err:          err_msg,
		ClientStart:  st,
		QueueStart:   op.Put.Start,
		End:          end,
		Clientid:     clientid,
		Optype:       "Write",
		Target:       cli.ActiveConnection().Target(),
	}

	println("CLIENT: Successfully put")

	res_ch <- resp
}

func get(res_ch chan *OpWire.Response, cli *clientv3.Client, op *OpWire.Operation_Get, clientid uint32) {
	//println("CLIENT: Attempting to get")
	st := unix_seconds(time.Now())
	_, err := cli.Get(context.Background(), string(op.Get.Key))
	end := unix_seconds(time.Now())

	err_msg := "None"
	if err != nil {
		err_msg = "ERROR WAS FOUND: " + err.Error()
	}

	resp := &OpWire.Response{
		ResponseTime: end - op.Get.Start,
		Err:          err_msg,
		ClientStart:  st,
		QueueStart:   op.Get.Start,
		End:          end,
		Clientid:     clientid,
		Optype:       "Read",
		Target:       cli.ActiveConnection().Target(),
	}

	println("CLIENT:Successfully got")

	res_ch <- resp
}

func check(e error) {
	if e != nil {
		log.Fatal(e)
	}
}

func marshall_response(resp *OpWire.Response) string {
	payload, err := proto.Marshal(resp)
	check(err)
	return string(payload)
}

func send(socket *zmq.Socket, msg string){
	socket.Send(msg, 0)
}

func recv_loop(quit_ch chan interface{}, res_ch chan *OpWire.Response, cli *clientv3.Client, clientid uint32){
	reader := bufio.NewReader(os.Stdin)

	for {
		println("Trying to read len")
		var size uint32
		if err := binary.Read(reader, binary.LittleEndian, &size); err != nil {
			log.Fatal(err)
		}

		fmt.Printf("Size = %v\n", size)

		payload := make([]byte, size)
		if _, err := io.ReadFull(reader, payload); err != nil {
			log.Fatal(err) }
		fmt.Printf("payload = \n%s\n-------", (hex.EncodeToString(payload)))

		println("Client: Received")
		op := &OpWire.Operation{}
		if err := proto.Unmarshal([]byte(payload), op); err != nil {
			log.Fatal("Failed to parse incomming operation")
		}
		switch op := op.OpType.(type) {
		case *OpWire.Operation_Put:
			go put(res_ch, cli, op, clientid)
		case *OpWire.Operation_Get:
			go get(res_ch, cli, op, clientid)
		case *OpWire.Operation_Quit:
			quit_ch <- true
			return
		default:
			resp := &OpWire.Response{
				ResponseTime: -1,
				Err:          fmt.Sprintf("Error: Operation (%v) was not found / supported", op),
				Clientid:     clientid,
				Optype:       "Error",
			}
			res_ch <- resp
		}
	}
}

func main() {
	println("Client: Starting client")

	endpoints := strings.Split(os.Args[1], ",")
	fmt.Printf("%v\n", endpoints)

	i, err := strconv.ParseUint(os.Args[2], 10, 32)
	check(err)
	address := "ipc://" + os.Args[3]

	clientid := uint32(i)

	socket, _ := zmq.NewSocket(zmq.DEALER)
	defer socket.Close()
	fmt.Printf("Client: connecting to: %s\n", address)
	socket.Connect(address)

	dialTimeout := 2 * time.Second

	cli, err := clientv3.New(clientv3.Config{
		Endpoints:            endpoints,
		DialTimeout:          dialTimeout,
		DialKeepAliveTime:    dialTimeout / 2,
		DialKeepAliveTimeout: dialTimeout * 2,
		AutoSyncInterval:     dialTimeout / 2,
	})
	defer cli.Close()
	check(err)

	println("Client: Sending ready signal")
	//send ready signal
	send(socket, "")

	res_ch := make(chan *OpWire.Response, 5)
	quit_ch := make(chan interface{}, 5)

	go recv_loop(quit_ch, res_ch, cli, clientid)

	for {
		select {
		case msg := <-res_ch:
			payload := marshall_response(msg)
			send(socket, payload)
		case <-quit_ch:
			return
		}
	}
}
