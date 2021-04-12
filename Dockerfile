FROM iwaseyusuke/mininet as base

RUN apt-get update && apt-get install --no-install-recommends -yy -qq \
    build-essential \
    software-properties-common

ADD Makefile Makefile

RUN make docker-build-deps

RUN ln /usr/bin/ovs-testcontroller /usr/bin/controller

RUN mkdir -p /results/logs

#ADD these here to cache the results of make docker-install-runtime-deps
ADD requirements.txt requirements.txt
ADD src src
RUN make docker-install-runtime-deps


ADD . .

COPY --from=etcd-image /system systems/etcd
