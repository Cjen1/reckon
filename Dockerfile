FROM cjen1/reckon-mininet:latest as base

RUN apt-get update && apt-get install --no-install-recommends -yy -qq \
    build-essential \
    software-properties-common

RUN ln /usr/bin/ovs-testcontroller /usr/bin/controller

# Cache docker-build-deps
ADD Makefile Makefile
RUN make docker-build-deps

RUN mkdir -p /results/logs

# Cache runtime deps
ADD requirements.txt requirements.txt
RUN make docker-install-runtime-deps

RUN apt update -y && apt install -y pv lsof vim

ADD . .

ENV PYTHONPATH="/root:${PYTHONPATH}"

COPY --from=etcd-image /reckon/systems/etcd systems/etcd
