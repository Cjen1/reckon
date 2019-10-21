.PHONY:install
install: etcd_install ocaml-paxos_install install-deps

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

build: distributions/message_pb2.py etcd_go utils/message_pb2.py

distributions/message_pb2.py: utils/message.proto
	protoc -I=utils --python_out=distributions/ utils/message.proto

utils/message_pb2.py: utils/message.proto
	protoc -I=utils --python_out=utils/ utils/message.proto

build: etcd

etcd: etcd/go 

etcd/go: systems/etcd/clients/go/client.go
	cd systems/etcd/clients/go && \
		make build 

template_go: template_docker systems/template/clients/go/client.go
	cd systems/template/clients/go && \
		make build 

.PHONY:install-deps
install-deps:
	sudo add-apt-repository ppa:deadsnakes/ppa -y
	echo "-------------status: updating----------------------"
	sudo apt update --yes
	echo "-------------status: upgrading---------------------"
	sudo DEBIAN_FRONTEND=noninteractive apt upgrade --yes
	echo "-------------status: installing--------------------"
	sudo apt install -y \
		python \
		python-numpy \
		python3.7 \
		python3-pip \
		autoconf \
		automake \
		libtool \
		curl \
		make \
		g++ \
		unzip \
		libzmq3-dev \
		tmux
	
	curl -L "https://github.com/protocolbuffers/protobuf/releases/download/v3.9.1/protoc-3.9.1-linux-x86_64.zip" >> /tmp/pb.zip
	unzip /tmp/pb.zip -d /tmp/pb
	sudo cp /tmp/pb/bin/protoc /usr/bin
	
	python -m pip install \
		protobuf \
		pyzmq \
		pathlib \
		tqdm \
		cgroups


#all: run_tests.py clients/*
##--------- setup proto files, gen config ----------
#
#config: libzmq4 libsodium
#
#libzmq4: 
#	wget https://github.com/zeromq/libzmq/releases/download/v4.2.3/zeromq-4.2.3.tar.gz -O build/zeromq-4.2.2.tar.gz 
#	cd build;\
#		tar -xvzf zeromq-4.2.2.tar.gz; \
#		sudo apt-get update && sudo apt-get install -y libtool pkg-config build-essential autoconf automake uuid-dev; \
#		cd zeromq-4.2.3; \
#		./configure; \
#		sudo make install; \
#		sudo ldconfig
#
#libsodium:
#	wget https://github.com/jedisct1/libsodium/releases/download/1.0.16/libsodium-1.0.16.tar.gz -O build/libsodium-1.0.16.tar.gz
#	cd build; \
#		tar -xvzf libsodium-1.0.16.tar.gz; \
#		cd libsodium-1.0.16; \
#		./configure; \
#		make && make check; \
#		sudo make install
#
#build/utils/message_pb2.py: utils/message.proto 
#	protoc -I=. --python_out=./build utils/message.proto
#
#build/utils/message.pb.go: utils/message.proto 
#	protoc -I . --go_out=./build utils/message.proto
#
#build/OpWire/Message.java: utils/message.proto
#	protoc -I . --java_out=./build utils/message.proto
#build/zookeeper_java-basic:
#	mkdir build/zookeeper_java-basic
#
#build/zookeeper_java-basic/external_classes: build/zookeeper_java-basic
#	cd build/zookeeper_java-basic; jar xf ../../jars/zookeeper-3.4.12.jar; jar xf ../../jars/com.google.protobuf.jar; jar xf ../../jars/com.neilalexander.jnacl.crypto.jar; \
#	jar xf ../../jars/org.zeromq.jar; jar xf ../../jars/slf4j.jar
#
##-------------- Tester Prerequisites --------------
#run_tests.py: utils/message_pb2.py
#
#utils/tester.py: utils/message_pb2.py
#
##-------------- etcd golang docker ----------------
#clients/etcd_go: etcd_go/client.go etcd_go/OpWire/message.pb.go 
#	go get github.com/pebbe/zmq4
#	go get go.etcd.io/etcd/clientv3
#	cd etcd_go ; \
#		go build -o ../clients/etcd_go client.go
#
#etcd_go/OpWire/message.pb.go: build/utils/message.pb.go
#	cp build/utils/message.pb.go etcd_go/OpWire
#
##-------------- etcd golang nodocker --------------
#clients/etcd-nodocker_go: etcd_go/client.go etcd_go/OpWire/message.pb.go 
#	go get github.com/pebbe/zmq4
#	go get go.etcd.io/etcd/clientv3
#	cd etcd_go ; \
#		go build -o ../clients/etcd-nodocker_go client.go
#
##-------------- consul golang prereq --------------
#
#clients/consul-progrium_go: consul_go/client.go consul_go/OpWire/message.pb.go
#	go get github.com/pebbe/zmq4
#	go get github.com/hashicorp/consul
#	cd consul_go ; \
#		go build -a -o ../clients/consul-progrium_go client.go
#
#clients/consul: consul_go/client.go consul_go/OpWire/message.pb.go
#	go get github.com/pebbe/zmq4
#	go get github.com/hashicorp/consul
#	cd consul_go ; \
#		go build -a -o ../clients/consul_go client.go
#
#consul_go/OpWire/message.pb.go: build/utils/message.pb.go
#	cp build/utils/message.pb.go consul_go/OpWire
#
##------------- zk java prereq ---------------------
#build/zookeeper_java-basic/OpWire/Message.class: build/OpWire/Message.java
#	cd build; javac -cp ".:../jars/com.google.protobuf.jar:../jars/zookeeper-3.4.12.jar:../jars/org.zeromq.jar:../jars/com.neilalexander.jnacl.crypto.jar" -d zookeeper_java-basic/ OpWire/Message.java
#
#build/zookeeper_java-basic/Client.class: zookeeper_java/Client.java build/zookeeper_java-basic/OpWire/Message.class
#	javac -cp ".:jars/com.google.protobuf.jar:jars/zookeeper-3.4.12.jar:jars/org.zeromq.jar:jars/com.neilalexander.jnacl.crypto.jar" -d build/zookeeper_java-basic/ zookeeper_java/Client.java;
#
#clients/zookeeper_java-basic.jar: build/zookeeper_java-basic/Client.class build/zookeeper_java-basic/external_classes
#	 mv build/zookeeper_java-basic clients; cd clients/zookeeper_java-basic; jar cvfe ../zookeeper_java-basic.jar zookeeper_java.Client *; cd ..; mv zookeeper_java-basic ../build;
#
#
#
#clients/exp: exp_go/client.go exp_go/OpWire/message.pb.go 
#	go get github.com/pebbe/zmq4; go get github.com/hashicorp/consul
#	cd exp_go; \
#		go build -a -o ../clients/exp client.go
#
#exp_go/OpWire/message.pb.go: build/utils/message.pb.go
#	cp build/utils/message.pb.go exp_go/OpWire
#
