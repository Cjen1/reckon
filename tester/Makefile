all: run_tests.py clients/*
#--------- setup proto files, gen config ----------

config: libzmq4 libsodium

libzmq4: 
	wget https://github.com/zeromq/libzmq/releases/download/v4.2.3/zeromq-4.2.3.tar.gz -O build/zeromq-4.2.2.tar.gz 
	cd build;\
		tar -xvzf zeromq-4.2.2.tar.gz; \
		sudo apt-get update && sudo apt-get install -y libtool pkg-config build-essential autoconf automake uuid-dev; \
		cd zeromq-4.2.3; \
		./configure; \
		sudo make install; \
		sudo ldconfig

libsodium:
	wget https://github.com/jedisct1/libsodium/releases/download/1.0.16/libsodium-1.0.16.tar.gz -O build/libsodium-1.0.16.tar.gz
	cd build; \
		tar -xvzf libsodium-1.0.16.tar.gz; \
		cd libsodium-1.0.16; \
		./configure; \
		make && make check; \
		sudo make install

build/utils/message_pb2.py: utils/message.proto 
	protoc -I=. --python_out=./build utils/message.proto

build/utils/message.pb.go: utils/message.proto 
	protoc -I . --go_out=./build utils/message.proto

OpWire/Message.java: utils/message.proto
	protoc -I . --java_out=. utils/message.proto

#------------ Generator prerequisites -------------

utils/link.py: utils/message_pb2.py

utils/message_pb2.py: build/utils/message_pb2.py 
	cp build/utils/message_pb2.py utils/message_pb2.py

#-------------- Tester Prerequisites --------------
run_tests.py: utils/message_pb2.py

utils/tester.py: utils/message_pb2.py

#-------------- etcd golang prereq ----------------

clients/etcd_go-basic: etcd_go/client.go etcd_go/OpWire/message.pb.go 
	go get github.com/pebbe/zmq4
	cd etcd_go ; \
		go build -o ../clients/etcd_go-basic client.go

etcd_go/OpWire/message.pb.go: build/utils/message.pb.go
	cp build/utils/message.pb.go etcd_go/OpWire

#-------------- consul golang prereq ----------------

clients/consul_go: consul_go/client.go consul_go/OpWire/message.pb.go 
	go get github.com/pebbe/zmq4
	cd consul_go ; \
		go build -a -o ../clients/consul_go client.go

consul_go/OpWire/message.pb.go: build/utils/message.pb.go
	cp build/utils/message.pb.go consul_go/OpWire

#------------- zk java prereq ---------------------
build/zookeeper_java-basic/OpWire/Message.class: OpWire/Message.java
	javac -cp ".:jars/com.google.protobuf.jar:jars/zookeeper-3.4.12.jar:jars/org.zeromq.jar:jars/com.neilalexander.jnacl.crypto.jar" -d build/zookeeper_java-basic/ OpWire/Message.java

build/zookeeper_java-basic/Client.class: zookeeper_java/Client.java build/zookeeper_java-basic/OpWire/Message.class
	javac -cp ".:jars/com.google.protobuf.jar:jars/zookeeper-3.4.12.jar:jars/org.zeromq.jar:jars/com.neilalexander.jnacl.crypto.jar" -d build/zookeeper_java-basic/ zookeeper_java/Client.java; mv build/zookeeper_java-basic clients

clients/zookeeper_java-basic.jar: build/zookeeper_java-basic/Client.class
	cd clients/zookeeper_java-basic; jar cvfe ../zookeeper_java-basic.jar zookeeper_java.Client *; cd ..; mv zookeeper_java-basic ../build;

experiment.txt: clients/zookeeper_java-basic.jar
	echo "TEst, teST" >> experiment.txt
