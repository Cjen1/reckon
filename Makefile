SHELL := /bin/bash

.PHONY:build docker runtest

build:
	docker build -t cjen1/rc:latest .

docker: build
	docker run -it --rm --privileged -e DISPLAY \
             -v /lib/modules:/lib/modules \
	     --network host --name rc_test \
	     --tmpfs /:rw \
	     cjen1/rc:latest

runtest: build
	docker run -it --rm --privileged -e DISPLAY \
             -v /lib/modules:/lib/modules \
	     --name resolving_consensus_test \
	     --network host \
	     cjen1/rc:latest ./scripts/run.sh &&\
	docker logs resolving_consensus_test 

