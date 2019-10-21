mn -c
killall java client etcd etcdctl screen
killall ocaml-paxos-acceptor ocaml-paxos-leader ocaml-paxos-replica 
rm -rf ./systems/zookeeper/scripts/zktmp/*
rm -rf ./utils/data/*
