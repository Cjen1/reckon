
ETCD_VER=v3.3.8
DOWNLOAD_URL=https://storage.googleapis.com/etcd

.PHONY: install
install: client etcd

.PHONY:etcd
system: etcd
etcd: /usr/bin/etcd /usr/bin/etcdctl

/usr/bin/etcd: /tmp/etcd-download
	sudo cp /tmp/etcd-download/etcd /usr/bin
	mkdir -p bin
	sudo cp /tmp/etcd-download/etcd bin/

/usr/bin/etcdctl: /tmp/etcd-download
	sudo cp /tmp/etcd-download/etcdctl /usr/bin
	mkdir -p systems/etcd/bin
	sudo cp /tmp/etcd-download/etcdctl systems/etcd/bin/

.PHONY:/tmp/etcd-download
/tmp/etcd-download:
	sudo rm -f /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
	sudo rm -rf /tmp/etcd-download && mkdir -p /tmp/etcd-download
	sudo curl -L ${DOWNLOAD_URL}/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz -o /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
	sudo tar xzvf /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz -C /tmp/etcd-download --strip-components=1
	sudo rm -f /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
	sudo cp /tmp/etcd-download/etcd /tmp/etcd-download/etcdctl /usr/bin


.PHONY:client
client:
	cd clients/go/ && make build
	cd clients/go-no-mem/ && make build
