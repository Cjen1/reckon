SHELL := /bin/bash

.PHONY:build docker runtest

build: protobuf
	docker build -t cjen1/rc:latest .

docker: build
	docker run -it --privileged -e DISPLAY \
             -v /lib/modules:/lib/modules \
	     --tmpfs /data \
	     --network host --name rc \
	     cjen1/rc:latest

docker-ssd: build
	docker run -it --privileged -e DISPLAY \
             -v /lib/modules:/lib/modules \
	     -v /local/scratch-ssd/cjj39/data:/data \
	     --network host --name rc \
	     cjen1/rc:latest


build-nocache: protobuf
	docker build --no-cache -t cjen1/rc:latest .


docker-nocache: build-nocache
	docker run -it --privileged -e DISPLAY \
             -v /lib/modules:/lib/modules \
	     --tmpfs /data \
	     --network host --name rc \
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
	cd src && make protobuf
