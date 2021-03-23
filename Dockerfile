FROM iwaseyusuke/mininet as base
ADD scripts/install/deps-Makefile Makefile
#ensure bashrc is used
SHELL ["/bin/bash", "-c", "-l"]

#Need correct controller
RUN ln /usr/bin/ovs-testcontroller /usr/bin/controller

ARG TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt update && apt install software-properties-common build-essential sudo tzdata -y

ADD scripts/install/deps-Makefile Makefile

RUN make pip

RUN make op-deps

RUN make zookeeper-deps

ENV GOPATH /root/go
ENV PATH $PATH:/usr/lib/go-1.11/bin
ENV PATH $PATH:/root/go/bin
RUN mkdir go
RUN make etcd-deps

ADD src/utils src/utils

#--------------------------------------------------
#- etcd -------------

FROM base as etcd_builder
ADD systems/etcd/Makefile systems/etcd/Makefile
RUN cd systems/etcd && make system
ADD systems/etcd/clients systems/etcd/clients
RUN cd systems/etcd && make client

#- benchmark --------

FROM golang:1.14 as benchmark 
RUN git clone https://github.com/etcd-io/etcd.git
RUN mkdir /etcdbin
RUN cd etcd && make && cp ./bin/* /etcdbin/
RUN cd etcd/tools/benchmark && go build -o /etcdbin/etcdbench 

##- ocaml ------------
#
#FROM base as ocaml_builder
#ENV OPAMYES=1
#RUN apt update && apt install liblapacke-dev libopenblas-dev zlib1g-dev -y
#ADD systems/ocaml-paxos/src/ocamlpaxos.opam systems/ocaml-paxos/src/ocamlpaxos.opam 
#RUN opam install --deps-only systems/ocaml-paxos/src -y
#ADD src/ocaml_client src/ocaml_client
#ADD src/utils/message.proto src/utils/message.proto 
#RUN cd src/ocaml_client && make install

##- ocaml-paxos ------
#
#FROM ocaml_builder as ocaml_paxos_builder
#ADD systems/ocaml-paxos/Makefile systems/ocaml-paxos/Makefile
#ADD systems/ocaml-paxos/src systems/ocaml-paxos/src
#ADD systems/ocaml-paxos/clients systems/ocaml-paxos/clients
#RUN cd systems/ocaml-paxos && make system
##Invalidate cache if client library has been updated
##COPY src/go/src/github.com/Cjen1/rc_go rc_go
##COPY src/go/src/github.com/Cjen1/rc_go go-deps
##COPY systems/ocaml-paxos/go go-deps
#RUN cd systems/ocaml-paxos && make client


#--------------------------------------------------
FROM base 

#- Install tools ----

RUN mkdir /results
RUN mkdir /results/logs

RUN mkdir bins logs
COPY --from=benchmark /etcdbin/etcdbench bins/
RUN echo 'export PATH=$PATH:~/bins/' >> ~/.bashrc

RUN git clone https://github.com/brendangregg/FlameGraph /results/FlameGraph

RUN apt update && apt install strace linux-tools-generic -y

ADD . .

#- Install binaries -
COPY --from=etcd_builder /root/systems/etcd systems/etcd
#COPY --from=ocaml_paxos_builder /root/systems/ocaml-paxos systems/ocaml-paxos
