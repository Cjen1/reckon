SHELL := /bin/bash

.PHONY: run
run: reckon
	docker run -it --privileged -e DISPLAY \
	     --tmpfs /data \
	     --network host --name reckon \
	     cjen1/reckon:latest

.PHONY:reckon
reckon: etcd-image
	docker build -t cjen1/reckon:latest .

.PHONY: etcd-image
etcd-image: protobuf
	cd systems/etcd && docker build -t etcd-image .

.PHONY: ocamlpaxos-image
ocamlpaxos-image:
	docker build -f Dockerfile.ocamlpaxos -t ocamlpaxos-image .

## ...etc

.PHONY: protobuf
protobuf:
	cd src && protoc -I=utils --python_out=utils utils/message.proto

.PHONY:python-deps
python-deps:
	pip install -r requirements.txt

.PHONY:docker-build-deps
docker-build-deps:
	apt-get install --no-install-recommends -yy -qq \
		python \
		python-pip \
		autoconf \
		automake \
		libtool \
		curl \
		g++ \
		unzip
	curl -L "https://github.com/protocolbuffers/protobuf/releases/download/v3.9.1/protoc-3.9.1-linux-x86_64.zip" > /tmp/pb.zip
	unzip /tmp/pb.zip -d /tmp/pb
	cp /tmp/pb/bin/protoc /usr/bin
	rm -r /tmp/pb

.PHONY:docker-install-runtime-deps
docker-install-runtime-deps: python-deps protobuf
	apt-get install --no-install-recommends -yy -qq \
		tmux \
		screen \
		psmisc \
		iptables \
		strace \
		linux-tools-generic \
		tcpdump
