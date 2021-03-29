SHELL := /bin/bash

.PHONY:build
build: protobuf
	docker build -t cjen1/reckon:latest .

.PHONY: docker
docker: build
	docker run -it --privileged -e DISPLAY \
	     --tmpfs /data \
	     --network host --name reckon \
	     cjen1/reckon:latest

.PHONY: protobuf
protobuf:
	cd src && make protobuf
