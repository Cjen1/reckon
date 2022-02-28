
install: build
	opam install .

build: rcclient/message.proto
	opam install ocaml-protoc
	opam install --deps-only .
	dune build

rcclient/message.proto: ../utils/message.proto
	cp ../utils/message.proto .
