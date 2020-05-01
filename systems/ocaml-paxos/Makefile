.PHONY: default system client
default: system client

system: 
	ls -la
	cd src && make
	mkdir bins
	cp src/_build/default/bin/main.exe bins/ocamlpaxos

client:
	cd clients/ocaml/ && make
