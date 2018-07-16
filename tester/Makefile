all: op_gen/op_gen.py 

#--------- setup proto files, gen config ----------

config: libzmq4 libsodium

proto: op_gen/message_pb2.py etcd_go/OpWire/message.pb.go

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

build/lib_pb/message_pb2.py: lib_pb/message.proto
	protoc -I=. --python_out=./build lib_pb/message.proto

build/lib_pb/message.pb.go: lib_pb/message.proto
	protoc -I . --go_out=./build lib_pb/message.proto
#------------ Generator prerequisites -------------

op_gen/op_gen.py: op_gen/link.py 

op_gen/link.py: op_gen/message_pb2.py

op_gen/message_pb2.py: build/lib_pb/message_pb2.py
	cp build/lib_pb/message_pb2.py op_gen/message_pb2.py

#-------------- etcd golang prereq ----------------

clients/etcd_go_basic: etcd_go/client.go etcd_go/OpWire/message.pb.go etcd_go/etcd_start.sh
	go get github.com/pebbe/zmq4
	cd etcd_go ; \
		go build -o ../clients/etcd_go_basic client.go

etcd_go/OpWire/message.pb.go: build/lib_pb/message.pb.go
	cp build/lib_pb/message.pb.go etcd_go/OpWire

etcd_go/etcd_start.sh: scripts/etcd_start.sh
	cp scripts/etcd_start.sh etcd_go



