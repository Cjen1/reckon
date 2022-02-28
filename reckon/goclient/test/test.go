package main

import rc_go "github.com/Cjen1/reckon/reckon/goclient"

type rc_cli struct {}

func (c rc_cli) Close() {}

func (c rc_cli) Put(k string, v string) (string, error) {
	return "unknown", nil
}

func (c rc_cli) Get(k string) (string, string, error) {
	return "N/A", "unknown", nil
}

func main() {
	gen_cli := func() (rc_go.Client, error){
		return rc_cli{}, nil
	}
	rc_go.Run(gen_cli, "test", false)
}
