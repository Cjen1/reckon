add-apt-repository ppa:deadsnakes/ppa -y
apt update 
apt upgrade -y
apt install -y \
	python \
	python-numpy \
	python3.7 \
	python3-pip \
	autoconf \
	automake \
	libtool \
	curl \
	make \
	g++ \
	unzip \
	libzmq3-dev \
	tmux

curl -L "https://github.com/protocolbuffers/protobuf/releases/download/v3.9.1/protoc-3.9.1-linux-x86_64.zip" >> /tmp/pb.zip
unzip /tmp/pb.zip -d /tmp/pb
cp /tmp/pb/bin/protoc /usr/bin

# Install instructions from github releases
ETCD_VER=v3.3.14

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

sudo add-apt-repository ppa:avsm/ppa
sudo apt update
sudo apt install opam

pip3 install --user \
	protobuf \
	pyzmq \
	pathlib \
	tqdm

pip install --user \
	protobuf \
	pyzmq \
	pathlib \
	tqdm 
