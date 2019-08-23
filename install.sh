RUN add-apt-repository ppa:deadsnakes/ppa -y \
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
	protobuf-compiler \
	tmux

pip3 install --user \
	protobuf \
	pyzmq \
	tqdm

pip install --user \
	protobuf \
	pyzmq \
	tqdm 
