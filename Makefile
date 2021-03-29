SHELL := /bin/bash

.PHONY: run
run: build
	docker run -it --privileged -e DISPLAY \
	     --tmpfs /data \
	     --network host --name reckon \
	     cjen1/reckon:latest

.PHONY: protobuf
protobuf:
	cd src && make protobuf

.PHONY: etcd-image
etcd-image:
	docker build -f Dockerfile.etcd -t etcd-image .

.PHONY: ocamlpaxos-image
ocamlpaxos-image:
	docker build -f Dockerfile.ocamlpaxos -t ocamlpaxos-image .

## ...etc

.PHONY:reckon
reckon: protobuf
	docker build -t cjen1/reckon:latest .
