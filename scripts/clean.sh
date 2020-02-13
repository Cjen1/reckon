sudo mn -c
sudo killall -9 client
sudo killall -9 etcd etcdctl
sudo killall -9 ocaml-paxos
rm -rf ../systems/zookeeper/scripts/zktmp/*
sudo rm -rf ../src/utils/data/*
sudo rm -rf ../src/utils/sockets/benchmark.sock
sudo rm -rf /data/*
