
.PHONY:client message.proto

build: client

client: client.ml message.proto
	eval `opam env`
	opam install ocaml-protoc hex -y
	dune build client.exe 
	cp _build/default/client.exe client

message.proto: ../../../../src/utils/message.proto
	cp ../../../../src/utils/message.proto .
