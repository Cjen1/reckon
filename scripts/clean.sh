# Clean mininet
sudo mn -c
# Clean up all processes from previous runs (TODO track from mininet?)
sudo killall -9 client
sudo killall -9 etcd etcdctl ocaml-paxos java
# Clean up zookeeper
rm -rf ../systems/zookeeper/scripts/zktmp/*
# Remove benchmark socket, to prevent mixing of data from runs
sudo rm -rf ../src/utils/sockets/benchmark.sock
