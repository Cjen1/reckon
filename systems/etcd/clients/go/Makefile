build: client

client: client.go OpWire/message.pb.go
	go get github.com/pebbe/zmq4
	go get github.com/golang/protobuf/proto
	#go get go.etcd.io/etcd/clientv3
	#go build -o ./client client.go

OpWire/message.pb.go: ../../../../src/utils/message.proto
	protoc -I ../../../../src/utils --go_out=OpWire ../../../../src/utils/message.proto
