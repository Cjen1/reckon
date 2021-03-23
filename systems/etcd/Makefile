
ETCD_VER=v3.4.14
DOWNLOAD_URL=https://storage.googleapis.com/etcd

.PHONY: install
install: client etcd

.PHONY:etcd
system:
	rm -f /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
	rm -rf /tmp/etcd-download && mkdir -p /tmp/etcd-download
	curl -L ${DOWNLOAD_URL}/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz -o /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
	tar xzvf /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz -C /tmp/etcd-download --strip-components=1
	rm -f /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
	mkdir -p bin
	cp /tmp/etcd-download/etcd bin/
	cp /tmp/etcd-download/etcdctl bin/

.PHONY:client
client:
	cd clients/go/ && make build
	cd clients/go-tracer && make build
