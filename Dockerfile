
FROM golang as benchmark 
RUN git clone https://github.com/etcd-io/etcd.git
RUN mkdir /etcdbin
RUN cd etcd && make && cp ./bin/* /etcdbin/
RUN cd etcd/tools/benchmark && go build -o /etcdbin/etcdbench 

FROM iwaseyusuke/mininet
#ensure bashrc is used
SHELL ["/bin/bash", "-c", "-l"]

#Need correct controller
RUN ln /usr/bin/ovs-testcontroller /usr/bin/controller

RUN apt update && apt install software-properties-common build-essential sudo -y

#-------- Install dependencies --------------------
ADD scripts/install/deps-Makefile Makefile

RUN make pip
RUN make etcd-deps
RUN make op-deps
RUN make zookeeper-deps

#-------- Install binaries ------------------------
ADD src/utils src/utils
ADD systems/etcd systems/etcd
RUN make etcd_install

ADD systems/zookeeper systems/zookeeper
RUN make zk_install

ADD systems/ocaml-paxos systems/ocaml-paxos
RUN make ocaml-paxos_install

#--------- Install tools --------------------------

ADD . .
RUN mkdir /results

RUN mkdir bins
COPY --from=benchmark /etcdbin/* bins/
RUN echo 'export PATH=$PATH:~/bins/' >> ~/.bashrc
