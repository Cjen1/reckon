package main

import (
	"context"
	"log"
	"strings"
	"time"
	"flag"
	"sync"

	"github.com/Cjen1/rc_go"
	"go.etcd.io/etcd/clientv3"
)

type myClient struct {
	clients []*clientv3.Client
	endpoints []string
	r_id int
	mtx *sync.Mutex
}

func (c myClient) get_client() (*clientv3.Client, string) {
	c.mtx.Lock()
	r_id := c.r_id
	c.r_id ++
	c.mtx.Unlock()
	id := r_id % len(c.clients)
	return c.clients[id],c.endpoints[id]
}

type rc_cli struct {
	Client myClient
}

func (c rc_cli) Close() {
	for _, c := range(c.Client.clients) {
		c.Close()
	}
}

func (c rc_cli) Put(k string, v string) (string, error) {
	client, target := c.Client.get_client()
	_, err := client.Put(context.Background(), k, v)
	return target, err
}

func (c rc_cli) Get(k string) (string, string, error) {
	client, target := c.Client.get_client()
	_, err := client.Get(context.Background(), k)
	return "", target, err
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
		clients := make([]*clientv3.Client, len(endpoints))
		for i, endpoint := range(endpoints) {
			client, err := clientv3.New(clientv3.Config{
				Endpoints:            []string{endpoint},
				DialTimeout:          dialTimeout,
				DialKeepAliveTime:    dialTimeout / 2,
				DialKeepAliveTimeout: dialTimeout * 2,
				AutoSyncInterval:     dialTimeout / 2,
			})
			if err != nil {
				return nil, err
			}
			clients[i] = client
		}
		cli := rc_cli{
			Client:myClient{
				clients:clients,
				endpoints:endpoints,
				r_id:0,
				mtx:&sync.Mutex{},
			},
		}
		return cli,nil
	}
	rc_go.Run(gen_cli, uint32(*f_client_id), *f_res_pipe, *f_new_client_per_request)
}
