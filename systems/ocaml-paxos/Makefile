.PHONY:install build client library
install: deps build 

build: client library

library:
	cd src && \
		make build
	rm -v ./bin/*
	cp ./src/_build/install/default/bin/* ./bin/

client: library
	cd clients/ocaml && \
		make build

.PHONY: deps opam
deps: opam
	sudo apt update -y
	sudo apt install -y \
	  libgmp-dev \
	  libzmq3-dev \
	  m4  \
	  perl \
	  libev-dev
	LWT_DISCOVER_ARGUMENTS="--use-libev true" opam install -y dune ounit core yojson uri ocaml-protoc zmq-lwt lwt_ppx utop logs fmt conf-libev
	eval `opam env`

opam:
	sudo add-apt-repository ppa:avsm/ppa -y
	sudo apt update -y
	sudo apt install opam -y
	opam init -a 
	opam switch ocaml-paxos
	#opam switch install ocaml-paxos ocaml-base-compiler.4.08.0
