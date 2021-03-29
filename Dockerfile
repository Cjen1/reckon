FROM iwaseyusuke/mininet as base

ARG TZ=Europe/London
RUN apt-get update && apt-get install --no-install-recommends -yy -qq \
    build-essential \
    software-properties-common \
    sudo \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN ln /usr/bin/ovs-testcontroller /usr/bin/controller

ADD scripts/install/deps-Makefile Makefile
RUN make pip

# RUN make zookeeper-deps ??? do you support ZK currently?

ADD src/utils src/utils

RUN mkdir -p \
    /results/logs \
    bins \
    logs

FROM benchmark-image as benchmark

RUN apt-get update && apt-get install --no-install-recommends -yy -qq \
    strace \
    linux-tools-generic
    && rm -rf /var/lib/apt/lists/*

COPY --from=benchmark /etcdbin/etcdbench bins/
RUN echo 'export PATH=$PATH:~/bins/' >> ~/.bashrc
RUN git clone https://github.com/brendangregg/FlameGraph /results/FlameGraph
## ...do you need to COPY --from=benchmark something due to above?

ADD . . ## given all teh selective ADDing until now, why this?

FROM etcd-image AS etcd
COPY --from=etcd /root/systems/etcd systems/etcd

FROM ocamlpaxos-image AS ocaml
COPY --from=ocaml_builder /root/systems/ocaml-paxos systems/ocaml-paxos

## ...etc for the other system that you build imgaes for elsewhere
