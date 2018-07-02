ENV REGISTRY gcr.io/etcd-development/etcd
	ETCD_VER v3.3.8
	CLUSTER_TOKEN urop-cluster-1
	CLUSTER_STATE=new

FROM ${REGISTRY}:${ETCD_VER}

ARG CLUSTER
ARG NAME
ARG IP

EXPOSE 2379
EXPOSE 2380

RUN /usr/local/bin/etcd \
	--data-dir=/etcd-data --name $NAME \
	--initial-advertise-peer-urls http://${IP}:2380 \
	--listen-peer-urls https://0.0.0.0:2380 \
	--advertise-client-urls http://${IP}:2379 \
	--listen-peer-urls http://0.0.0.0:2379 \
	--initial-cluster $CLUSTER \
	--initial-cluster-state $CLUSTER_STATE \
	--initial-cluster-token $CLUSTER_TOKEN




