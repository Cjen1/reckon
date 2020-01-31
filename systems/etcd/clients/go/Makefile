
.PHONY:client OpWire/message.pb.go

build: client

client: client.go OpWire/message.pb.go
	#go get github.com/pebbe/zmq4
	#go get github.com/golang/protobuf/proto
	#go get go.etcd.io/etcd/clientv3
	/usr/lib/go-1.11/bin/go build -o ./client client.go

OpWire/message.pb.go: ../../../../src/utils/message.proto
	protoc -I ../../../../src/utils --go_out=OpWire ../../../../src/utils/message.proto
