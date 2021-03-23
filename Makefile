SHELL := /bin/bash

.PHONY:build docker runtest

build: protobuf
	docker build -t cjen1/reckon:latest .

#docker: build
#	docker run -it --privileged -e DISPLAY \
#             -v /lib/modules:/lib/modules \
#	     --tmpfs /data \
#	     --network host --name reckon \
#	     cjen1/reckon:latest

docker: build
	docker run -it --privileged -e DISPLAY \
	     --tmpfs /data \
	     --network host --name reckon \
	     cjen1/reckon:latest

.PHONY: protobuf
protobuf:
	cd src && make protobuf
