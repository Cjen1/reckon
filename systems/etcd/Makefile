
ETCD_VER=v3.4.14
DOWNLOAD_URL=https://storage.googleapis.com/etcd

.PHONY: install
install: client etcd

.PHONY:etcd
system: etcdVariants
	rm -f /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
	rm -rf /tmp/etcd-download && mkdir -p /tmp/etcd-download
	curl -L ${DOWNLOAD_URL}/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz -o /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
	tar xzvf /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz -C /tmp/etcd-download --strip-components=1
	rm -f /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
	mkdir -p bin
	cp /tmp/etcd-download/etcd bin/
	cp /tmp/etcd-download/etcdctl bin/

etcdVariants:
	mkdir -p bin
	cd altered_etcd_source \
		&& git checkout NoCheckQuorum \
		&& ETCD_SETUP_GOPATH=1 make build \
		&& cp bin/etcd ../bin/etcd_sans_check_quorum
	cd altered_etcd_source \
		&& git checkout debug \
		&& ETCD_SETUP_GOPATH=1 make build \
		&& cp bin/etcd ../bin/etcd_debug

.PHONY:client
client:
	cd clients/go/ && make build
	cd clients/go-no-mem/ && make build
