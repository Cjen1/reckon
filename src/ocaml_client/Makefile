
install: build
	opam install .

build: rcclient/message.proto
	opam install ocaml-protoc -y
	dune build

rcclient/message.proto: ../utils/message.proto
	cp ../utils/message.proto .
