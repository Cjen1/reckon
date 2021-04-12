FROM golang:1.13

ADD message.proto /system/utils/message.proto
ADD Makefile /system/Makefile
RUN cd /system && make docker-build-deps

RUN cd /system && make system
ADD clients /system/clients
RUN cd /system && make client
