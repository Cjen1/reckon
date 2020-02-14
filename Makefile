SHELL := /bin/bash

.PHONY:build docker runtest

build:
	docker build -t cjen1/rc:latest .

docker: build
	docker run -it --rm --privileged -e DISPLAY \
             -v /lib/modules:/lib/modules \
	     --tmpfs /data \
	     --network host --name rc_test \
	     cjen1/rc:latest

runtest: build
	docker run -it --rm --privileged -e DISPLAY \
             -v /lib/modules:/lib/modules \
	     -v /local/scratch-ssd/cjj39/data:/data \
	     --name resolving_consensus_test \
	     --network host \
	     cjen1/rc:latest ./scripts/run.sh &&\
	docker logs resolving_consensus_test 

.PHONY: protobuf
protobuf:
	cd src && make build
