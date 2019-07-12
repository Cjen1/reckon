from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel

def setup(dockers, ips):
    cluster = "".join("etcd-node-"+str(i+1) + "=http://"+ip+":2380," for i, ip in enumerate(ips))[:-1]

    for i, (docker, ip) in enumerate(zip(dockers, ips)):
        node_name = "etcd-node-"+str(i+1)
        docker.cmd(
                    (  
                    "screen -d -S etcd_background -m /usr/local/bin/etcd " +
                    "--data-dir=/etcd-data --name {name} " + 
                    "--initial-advertise-peer-urls http://{ip}:2380 --listen-peer-urls http://0.0.0.0:2380 " + 
                    "--advertise-client-urls http://{ip}:2379 --listen-client-urls http://0.0.0.0:2379 " + 
                    "--initial-cluster {cluster} " +
                    "--initial-cluster-state {cluster_state} --initial-cluster-token {cluster_token}" +
                    "&"
                    ).format(
                        name=node_name, 
                        ip=ip, 
                        cluster=cluster, 
                        cluster_state="new", 
                        cluster_token="urop_cluster"
                    )
                )


