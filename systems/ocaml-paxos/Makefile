.PHONY:install build client library
build: client library

library:
	#rm -vrf ./src/_build/*
	cd src && \
		make build
	rm -v ./bin/*
	cp ./src/_build/install/default/bin/* ./bin/

client: library
	cd clients/ocaml && \
		make build
