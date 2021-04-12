
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

.PHONY:docker-build-deps
docker-build-deps:
	apt-get update && apt-get install --no-install-recommends -yy -qq \
		unzip
	curl -L "https://github.com/protocolbuffers/protobuf/releases/download/v3.9.1/protoc-3.9.1-linux-x86_64.zip" > /tmp/pb.zip
	unzip /tmp/pb.zip -d /tmp/pb
	cp /tmp/pb/bin/protoc /usr/bin
	rm -r /tmp/pb
	go get google.golang.org/protobuf/cmd/protoc-gen-go
