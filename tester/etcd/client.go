package main

import (
	"log"
	"time"
	"context"

	"github.com/coreos/etcd/client"
)

func receiveOp() {

}

func sendResp() {

}

func put(kapi, Op) {
	// Todo implement options
	st = time.Now()
	resp, err := kapi.Set(context.Background(), Op.getKey(), Op.getVal(), nil)
	duration = time.Since(st)

	// Todo implement response_obj
	return response_obj
}

func get(kapi, Op) {
	// Todo implement options
	st = time.Now()
	resp, err := kapi.Get(context.Background(), Op.getKey(), nil)
	duration = time.Since(st)

	return response_obj
}

func setup(Op) {
	cfg := client.Config{
		Endpoints: 		Op.getEndpoints(),
		Transport:		client.DefaultTransport,
		HeaderTimeoutPerRequest: time.Second,
	}

	c, err := client.New(cfg)
	if err != nil {
		log.Fatal(err)
	}

	kapi := client.NewKeysAPI(c)

	return response_obj, cfg, kapi
}


func main() {
	for {

		Op := receiveOp()

		var resp
		switch Op.type {
		case Op.setup:
			resp, cfg, kapi = setup(Op)
		case Op.put:
			put(kapi, Op)
		case Op.quit:
			return
		}
	}
}
	

	
