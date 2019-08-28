#- ETCD ---------------
# Install instructions from github releases

ETCD_VER=v3.3.8

# choose either URL
GOOGLE_URL=https://storage.googleapis.com/etcd
GITHUB_URL=https://github.com/etcd-io/etcd/releases/download
DOWNLOAD_URL=${GOOGLE_URL}

rm -f /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
rm -rf /tmp/etcd-download-test && mkdir -p /tmp/etcd-download-test

curl -L ${DOWNLOAD_URL}/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz -o /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz
tar xzvf /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz -C /tmp/etcd-download-test --strip-components=1
rm -f /tmp/etcd-${ETCD_VER}-linux-amd64.tar.gz

cp /tmp/etcd-download-test/etcd /tmp/etcd-download-test/etcdctl /usr/bin

add-apt-repository ppa:gophers/archive
apt update
apt install -y golang-1.11-go
echo 'export GOPATH=~/go' >> ~/.bashrc
echo 'export PATH=$PATH:~/go/bin' >> ~/.bashrc
echo 'export PATH=$PATH:/usr/lib/go-1.11/bin' >> ~/.bashrc
/usr/lib/go-1.11/bin/go get -u github.com/golang/protobuf/protoc-gen-go
