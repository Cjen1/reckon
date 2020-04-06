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
ADD systems/etcd/clients systems/etcd/clients
ADD systems/etcd/Makefile systems/etcd/Makefile
RUN make etcd_install

#- ocaml-paxos ------

FROM base as ocaml_paxos_builder
ADD systems/ocaml-paxos systems/ocaml-paxos
RUN make ocaml-paxos_install

#- benchmark --------

FROM golang as benchmark 
RUN git clone https://github.com/etcd-io/etcd.git
RUN mkdir /etcdbin
RUN cd etcd && make && cp ./bin/* /etcdbin/
RUN cd etcd/tools/benchmark && go build -o /etcdbin/etcdbench 

FROM base 

#-------- Install binaries ------------------------
COPY --from=etcd_builder /root/systems/etcd systems/etcd
COPY --from=ocaml_paxos_builder /root/systems/ocaml-paxos systems/ocaml-paxos

#ADD systems/zookeeper systems/zookeeper
#RUN make zk_install

#--------- Install tools --------------------------

RUN mkdir /results

RUN mkdir bins logs
COPY --from=benchmark /etcdbin/* bins/
RUN echo 'export PATH=$PATH:~/bins/' >> ~/.bashrc

ADD . .
