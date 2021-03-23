package main

import (
	"context"
	"log"
	"strings"
	"time"
	"flag"

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
	f_endpoints := flag.String("targets", "", "Endpoints to send to ie: http://127.0.0.1:4000, http://127.0.0.1:4001")
	f_client_id := flag.Int("id", -1, "Client id")
	f_new_client_per_request := flag.Bool("ncpr", false, "New client per request")
	f_res_pipe := flag.String("results", "", "Result file")

	flag.Parse()

	endpoints := strings.Split(*f_endpoints, ",")
	log.Printf("%v\n", endpoints)

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
	rc_go.Run(gen_cli, uint32(*f_client_id), *f_res_pipe, *f_new_client_per_request)
}
