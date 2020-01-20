SHELL := /bin/bash

.PHONY:build docker runtest

build:
	docker build -t cjen1/rc:latest .

docker: build
	docker run -it --rm --privileged -e DISPLAY \
             -v /lib/modules:/lib/modules \
	     --network host --name rc_test \
	     cjen1/rc:latest

runtest: build
	docker run -it --rm --privileged -e DISPLAY \
             -v /lib/modules:/lib/modules \
	     --name resolving_consensus_test \
	     --network host \
	     cjen1/rc:latest ./scripts/run.sh &&\
	docker logs resolving_consensus_test 

.PHONY:install
install: etcd_install ocaml-paxos_install zk_install

.PHONY:etcd_install
etcd_install: 
	cd systems/etcd && \
		make install

.PHONY:ocaml-paxos_install
ocaml-paxos_install:
	cd systems/ocaml-paxos && \
		make install

.PHONY:zk_install
zk_install:
	cd systems/zookeeper && \
		make install

build-deps: utils/message_pb2.py etcd_go

utils/message_pb2.py: utils/message.proto
	protoc -I=utils --python_out=utils/ utils/message.proto

etcd: etcd_go 

etcd_go: systems/etcd/clients/go/client.go
	cd systems/etcd/clients/go && \
		make build 

template_go: template_docker systems/template/clients/go/client.go
	cd systems/template/clients/go && \
		make build 

