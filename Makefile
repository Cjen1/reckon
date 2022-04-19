SHELL := /bin/bash

.PHONY: run
run: reckon
	docker run -it --privileged -e DISPLAY \
	     --tmpfs /data \
	     --network host --name reckon \
	     cjen1/reckon:latest bash

.PHONY: lossy-etcd
lossy-etcd: reckon
	docker run -it --privileged -e DISPLAY \
		--tmpfs /data \
		--network host --name reckon \
		cjen1/reckon:latest ./scripts/run.sh python ./scripts/lossy_etcd.py

.PHONY:reckon
reckon: reckon-mininet etcd-image
	docker build -t cjen1/reckon:latest .

.PHONY: reckon-mininet
reckon-mininet: 
	docker build -f Dockerfile.mininet -t cjen1/reckon-mininet:latest .

.PHONY: etcd-image
etcd-image:
	docker build -f Dockerfile.etcd -t etcd-image .

.PHONY: ocamlpaxos-image
ocamlpaxos-image:
	docker build -f Dockerfile.ocamlpaxos -t ocamlpaxos-image .

.PHONY:python-deps
python-deps:
	pip3 install --upgrade wheel setuptools
	pip3 install -r requirements.txt

.PHONY:docker-build-deps
docker-build-deps:
	apt-get update
	apt-get install --no-install-recommends -yy -qq \
		autoconf \
		automake \
		libtool \
		curl \
		g++ \
		unzip

.PHONY:docker-install-runtime-deps
docker-install-runtime-deps: python-deps 
	apt-get install --no-install-recommends -yy -qq \
		tmux \
		screen \
		psmisc \
		iptables \
		strace \
		linux-tools \
		tcpdump
