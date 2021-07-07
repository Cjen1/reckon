# Clean up state

# Clean mininet
mn -c
# Clean up all processes from previous runs (TODO track from mininet?)
killall -9 client
killall -9 etcd etcdctl ocaml-paxos
# Clean up zookeeper
rm -rf ../systems/zookeeper/scripts/zktmp/*
# Remove benchmark socket, to prevent mixing of data from runs
rm -rf ../src/utils/sockets/benchmark.sock
# Remove temporary data
rm -rf /data/*
