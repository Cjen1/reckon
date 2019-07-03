from subprocess import call
from sys import argv
from socket import gethostbyname

hosts = argv[1].split(",")

def setup_remote(host, ip, node_name):
    cluster = "".join("etcd-node-" + str(i+1) + "=http://" + host + ":2380," for i, host in enumerate(hosts))[:-1]
    call([
        "ssh",
        host,
        (   "screen -d -S etcd_background -m " +
            "./go/bin/etcd " +
            "--data-dir=etcd_data --name {name} " + 
            "--initial-advertise-peer-urls http://127.0.1.1:2380 --listen-peer-urls http://0.0.0.0:2380 " + 
            "--advertise-client-urls http://{ip}:2379 --listen-client-urls http://0.0.0.0:2379 " + 
            "--initial-cluster {cluster} " +
            "--initial-cluster-state {cluster_state} --initial-cluster-token {cluster_token}"
        ).format(
            registry="gcr.io/etcd-development/etcd", 
            etcd_ver="v3.3.8", 
            name=node_name, 
            ip=ip, 
            cluster=cluster, 
            cluster_state="new", 
            cluster_token="urop_cluster")
        ])

for i, host in enumerate(hosts):
    setup_remote(host, gethostbyname(host), "etcd-node-" + str(i+1))

