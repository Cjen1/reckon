GC = go

all: op_gen/op_gen.py 

#------------ Generator prerequisites -------------

op_gen/op_gen.py: op_gen/link.py

op_gen/link.py: op_gen/message_pb2.py

op_gen/message_pb2.py: lib_pb/message.proto
	protoc -I=. --python_out=./build lib_pb/message.proto
	cp build/lib_pb/message_pb2.py op_gen/message_pb2.py

#-------------- etcd golang prereq ----------------

etcd_go/client: etcd_go/client.go etcd_go/


