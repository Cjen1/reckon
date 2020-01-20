FROM golang as benchmark 
RUN git clone https://github.com/etcd-io/etcd.git
RUN mkdir /etcdbin
RUN cd etcd && make && cp ./bin/* /etcdbin/
RUN cd etcd/tools/benchmark && go build -o /etcdbin/etcdbench 

FROM iwaseyusuke/mininet

#Need correct controller
RUN ln /usr/bin/ovs-testcontroller /usr/bin/controller

RUN apt update && apt install software-properties-common build-essential sudo -y

ADD scripts/install/Makefile .

#Set up and activate venv
#RUN apt install python3-venv -y
#ENV VIRTUAL_ENV=/root/env
#RUN python3 -m venv $VIRTUAL_ENV
#ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN make etcd-deps
RUN make op-deps
RUN make pip
RUN make zookeeper-deps

ADD systems systems
Add Makefile Makefile

RUN make etcd_install
RUN make zk_install
RUN make ocaml-paxos_install

ADD . .
RUN mkdir /results

RUN mkdir bins
COPY --from=benchmark /etcdbin/* bins/
RUN echo 'export PATH=$PATH:~/bins/' >> ~/.bashrc
