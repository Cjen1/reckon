build: client

capnp-rpc: 
	cd deps/capnp-rpc && \
		opam install .

library: 
	cd src && \
		make build

client: library
	cd clients/ocaml && \
		make build
