
.PHONY: install
install: client etcd

.PHONY:etcd
system: 
	cd ocons && make build
	mkdir bins
	cp ocons/_build/install/default/bin/* bins/

.PHONY:client
client: client-deps
	cd clients/ocaml && make build

.PHONY: client-deps
client-deps:
	cd clients/ocaml && opam install --deps-only --yes .
	rm -rf clients/ocaml/ocons
	cp -r ocons clients/ocaml/ocons
