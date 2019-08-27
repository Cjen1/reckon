add-apt-repository ppa:gophers/archive
apt update
apt install -y golang-1.11-go
echo 'export GOPATH=~/go' >> ~/.bashrc
echo 'export PATH=$PATH:~/go/bin' >> ~/.bashrc
echo 'export PATH=$PATH:/usr/lib/go-1.11/bin' >> ~/.bashrc
/usr/lib/go-1.11/bin/go get -u github.com/golang/protobuf/protoc-gen-go
