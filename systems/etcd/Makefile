install: etcd-install go-install

etcd-install: /usr/bin/etcd /usr/bin/etcdctl

/usr/bin/etcd: /tmp/etcd-download
	sudo cp /tmp/etcd-download/etcd /usr/bin

/usr/bin/etcdctl: /tmp/etcd-download
	sudo cp /tmp/etcd-download/etcdctl /usr/bin

.PHONY:/tmp/etcd-download go-install

ETCD_VER=v3.3.8
DOWNLOAD_URL=https://storage.googleapis.com/etcd

/tmp/etcd-download:
	sudo rm -f /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
	sudo rm -rf /tmp/etcd-download && mkdir -p /tmp/etcd-download
	sudo curl -L ${DOWNLOAD_URL}/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz -o /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
	sudo tar xzvf /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz -C /tmp/etcd-download --strip-components=1
	sudo rm -f /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
	sudo cp /tmp/etcd-download/etcd /tmp/etcd-download/etcdctl /usr/bin

go-install:
	sudo add-apt-repository ppa:gophers/archive -y
	sudo apt update
	sudo apt install -y golang-1.11-go
	echo 'export GOPATH=~/go' >> ~/.bashrc
	echo 'export PATH=$PATH:~/go/bin' >> ~/.bashrc
	echo 'export PATH=$PATH:/usr/lib/go-1.11/bin' >> ~/.bashrc
	sudo /usr/lib/go-1.11/bin/go get -u github.com/golang/protobuf/protoc-gen-go



