package main

import (
	"context"
	"log"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/Cjen1/rc_go"
	"go.etcd.io/etcd/clientv3"
)

type rc_cli struct {
	Client *clientv3.Client
}

func (c rc_cli) Close() {
	c.Client.Close()
}

func (c rc_cli) Put(k string, v string) error {
	_, err := c.Client.Put(context.Background(), k, v)
	return err
}

func (c rc_cli) Get(k string) (string, error) {
	_, err := c.Client.Get(context.Background(), k)
	return "", err
}

func main() {
	log.Print("Client: Starting client memory client")

	endpoints := strings.Split(os.Args[1], ",")
	log.Printf("%v\n", endpoints)

	i, err := strconv.ParseUint(os.Args[2], 10, 32)
	if err != nil {
		log.Fatal(err)
	}
	clientid := uint32(i)

	log.Printf("Client: creating file")
	result_pipe := os.Args[3]

	dialTimeout := 10 * time.Second

	gen_cli := func() (rc_go.Client, error){
		cli_v3, err := clientv3.New(clientv3.Config{
			Endpoints:            endpoints,
			DialTimeout:          dialTimeout,
			DialKeepAliveTime:    dialTimeout / 2,
			DialKeepAliveTimeout: dialTimeout * 2,
			AutoSyncInterval:     dialTimeout / 2,
		})
		cli := rc_cli{Client:cli_v3}
		return cli,err
	}
	rc_go.Run(gen_cli, clientid, result_pipe, false, false)
}
