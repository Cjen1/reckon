SHELL := /bin/bash

.PHONY: run
run: reckon
	docker run -it --privileged -e DISPLAY \
	     --tmpfs /data \
	     --network host --name reckon \
	     cjen1/reckon:latest

.PHONY:reckon
reckon: etcd-image ocons-image
	docker build -t cjen1/reckon:latest .

.PHONY: etcd-image
etcd-image:
	cd systems/etcd && docker build -t etcd-image .

.PHONY: ocons-image
ocons-image:
	cd systems/ocons && docker build -t ocons-image .

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
	apt-get update 
	apt-get install --no-install-recommends -yy -qq \
		tmux \
		screen \
		psmisc \
		iptables \
		strace \
		linux-tools-generic \
		tcpdump
	TZ="Europe/London" DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata
	pip install pandas
