FROM iwaseyusuke/mininet as base

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
ADD src src
RUN make docker-install-runtime-deps

ADD . .

COPY --from=etcd-image /system systems/etcd
