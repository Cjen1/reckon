SHELL := /bin/bash

.PHONY: run
run: reckon
	docker run -it --privileged -e DISPLAY \
	     --tmpfs /data \
	     --network host --name reckon \
	     cjen1/reckon:latest bash

.PHONY: etcd
etcd: reckon
	docker run -it --privileged -e DISPLAY \
		--tmpfs /data --rm \
		--network host --name reckon-etcd \
		cjen1/reckon:latest ./scripts/run.sh python -m reckon etcd simple uniform none

.PHONY: lossy-etcd
lossy-etcd: reckon
	docker run -it --privileged -e DISPLAY \
		--tmpfs /data \
		--network host --name reckon \
		cjen1/reckon:latest ./scripts/run.sh python ./scripts/lossy_etcd.py

.PHONY:reckon
reckon: reckon-mininet etcd-image zk-image
		docker build -t cjen1/reckon:latest .

.PHONY: reckon-mininet
reckon-mininet: 
	docker build -f Dockerfile.mininet -t cjen1/reckon-mininet:latest .

.PHONY: etcd-image
etcd-image:
		docker build -f Dockerfile.etcd -t etcd-image .

.PHONY: zk-image
zk-image:
		docker build -f Dockerfile.zookeeper -t zk-image .

.PHONY: ocamlpaxos-image
ocamlpaxos-image:
	docker build -f Dockerfile.ocamlpaxos -t ocamlpaxos-image .
