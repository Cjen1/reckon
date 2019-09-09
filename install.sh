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


pip3 install --user \
	protobuf \
	pyzmq \
	pathlib \
	tqdm \
	cgroups

pip install --user \
	protobuf \
	pyzmq \
	pathlib \
	tqdm \
	cgroups
