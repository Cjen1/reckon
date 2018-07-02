FROM gcr.io/etcd-development/etcd:v3.3.8

ENV	CLUSTER_TOKEN urop-cluster-1
ENV	CLUSTER_STATE new

ARG CLUSTER
ENV CLUSTER=$CLUSTER
ARG NAME
ENV NAME=$NAME
ARG IP
ENV IP=$IP

EXPOSE 2379
EXPOSE 2380

ENTRYPOINT /usr/local/bin/etcd --data-dir=/etcd-data --name $NAME --initial-advertise-peer-urls http://${IP}:2380 --listen-peer-urls http://0.0.0.0:2380 --advertise-client-urls http://${IP}:2379 --listen-peer-urls http://0.0.0.0:2379 --initial-cluster $CLUSTER --initial-cluster-state $CLUSTER_STATE --initial-cluster-token $CLUSTER_TOKEN
