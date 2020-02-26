.PHONY:client OpWire/message.pb.go

build: client

client: client.go OpWire/message.pb.go PaxWire/client.pb.go
	/usr/lib/go-1.11/bin/go build -o ./client client.go

OpWire/message.pb.go: ../../../../src/utils/message.proto
	protoc -I ../../../../src/utils --go_out=OpWire ../../../../src/utils/message.proto

PaxWire/client.pb.go: ../../src/lib/client.proto
	protoc -I ../../src/lib/ --go_out=PaxWire ../../src/lib/client.proto
