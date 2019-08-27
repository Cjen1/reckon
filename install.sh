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

curl "https://github-production-release-asset-2e65be.s3.amazonaws.com/23357588/f2180400-b852-11e9-85ff-163c511143d7?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIWNJYAX4CSVEH53A%2F20190826%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20190826T091337Z&X-Amz-Expires=300&X-Amz-Signature=cbb24f81e8d8e0358e5940ef499fbc12c9258b8bf254456504f9e1f9ca7b5a78&X-Amz-SignedHeaders=host&actor_id=11444677&response-content-disposition=attachment%3B%20filename%3Dprotoc-3.9.1-linux-x86_64.zip&response-content-type=application%2Foctet-stream" >> /tmp/pb.zip
unzip /tmp/pb.zip -d /tmp/pb
cp /tmp/pb/bin/protoc /usr/bin

curl "https://github-production-release-asset-2e65be.s3.amazonaws.com/11225014/803fb180-c279-11e9-829c-d96e4f93a03f?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIWNJYAX4CSVEH53A%2F20190826%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20190826T103922Z&X-Amz-Expires=300&X-Amz-Signature=8ccfd635cf9027dd29db7cc7775546febe4e5af66a33444fbaad03a209e07001&X-Amz-SignedHeaders=host&actor_id=11444677&response-content-disposition=attachment%3B%20filename%3Detcd-v3.3.15-linux-amd64.tar.gz&response-content-type=application%2Foctet-stream" >> /tmp/etcd.tar.gz
tar -xf /tmp/etcd.tar.gz -C /tmp/etcd-install
cp /tmp/etcd-install/etcd /tmp/etcd-install/etcdctl /usr/bin

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
