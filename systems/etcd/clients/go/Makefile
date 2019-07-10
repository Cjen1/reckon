build: client

client: client.go OpWire/message.pb.go
	go get github.com/pebbe/zmq4
	go get github.com/golang/protobuf/proto
	go get go.etcd.io/etcd/clientv3
	go build -o ./client client.go

OpWire/message.pb.go: ../../../../utils/message.proto gen-go
	protoc -I ../../../../utils --go_out=OpWire ../../../../utils/message.proto

gen-go:
	go get -u github.com/golang/protobuf/protoc-gen-go
