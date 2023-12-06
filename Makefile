SHELL := /bin/bash

.PHONY: run
run: reckon
	docker run -it --privileged -e DISPLAY \
	--tmpfs /data \
	--network host --name reckon \
	 cjen1/reckon:latest bash

.PHONY: tester
tester: reckon
	docker run -it --privileged -e DISPLAY \
	--tmpfs /data \
	--network host --name reckon \
	 cjen1/reckon:latest bash /root/scripts/run.sh python /root/scripts/tester.py

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
