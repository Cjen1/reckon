
.PHONY: install
install: client etcd

.PHONY:etcd
system:
	cd ocons && dune install

.PHONY:client
client:
	cd clients/go/ && make build
	cd clients/go-tracer && make build
