all: test.py

#--------- setup proto files, gen config ----------

config: libzmq4 libsodium

proto: utils/message_pb2.py etcd_go/OpWire/message.pb.go

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

#----------- Test Infra prerequisites -------------

test.py: utils/op_gen.py proto

#------------ Generator prerequisites -------------

utils/link.py: utils/message_pb2.py

utils/message_pb2.py: build/utils/message_pb2.py
	cp build/utils/message_pb2.py utils/message_pb2.py

#-------------- etcd golang prereq ----------------

clients/etcd_go-basic: etcd_go/client.go etcd_go/OpWire/message.pb.go 
	go get github.com/pebbe/zmq4
	cd etcd_go ; \
		go build -o ../clients/etcd_go-basic client.go

etcd_go/OpWire/message.pb.go: build/utils/message.pb.go
	cp build/utils/message.pb.go etcd_go/OpWire

#-------------- consul golang prereq ----------------

clients/consul_go-basic: consul_go/client.go consul_go/OpWire/message.pb.go 
	go get github.com/pebbe/zmq4
	cd consul_go ; \
		go build -a -o ../clients/consul_go-basic client.go

consul_go/OpWire/message.pb.go: build/utils/message.pb.go
	cp build/utils/message.pb.go consul_go/OpWire
#------------- zk java prereq ---------------------
clients/zookeeper_java/OpWire/Message.class: zookeeper_java/OpWire/Message.java
	javac -cp ".:/home/dks28/Zookeeper/tester/jars/com.google.protobuf.jar:/home/dks28/Zookeeper/tester/jars/zookeeper-3.4.12.jar:/home/dks28/Zookeeper/tester/jars/org.zeromq.jar:/home/dks28/Zookeeper/tester/jars/com.neilalexander.jnacl.crypto.jar" -d clients/zookeeper_java-basic/OpWire zookeeper_java/OpWire/Message.java

clients/zookeeper_java-basic/Client.class: zookeeper_java/Client.java clients/zookeeper_java/OpWire/Message.class
	javac -cp ".:/home/dks28/Zookeeper/tester/jars/com.google.protobuf.jar:/home/dks28/Zookeeper/tester/jars/zookeeper-3.4.12.jar:/home/dks28/Zookeeper/tester/jars/org.zeromq.jar:/home/dks28/Zookeeper/tester/jars/com.neilalexander.jnacl.crypto.jar" -d clients/zookeeper_java-basic/ zookeeper_java/Client.java

clients/zookeeper_java-basic.jar: clients/zookeeper_java-basic/Client.class
	cd clients/zookeeper_java-basic; jar cvfe /home/dks28/Zookeeper/tester/clients/zookeeper_java-basic.jar zookeeper_java.Client *
