from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel

def setup(dockers, ips):
    cluster = "".join("etcd-node-"+str(i+1) + "=http://"+ip+":2380," for i, ip in enumerate(ips))[:-1]

    restarters = []

    print(dockers)
    print(ips)
    for i, (docker, ip) in enumerate(zip(dockers, ips)):
        node_name = "etcd-node-"+str(i+1)

        start_cmd = (
                    "screen -d -S etcd -m etcd " +
                    "--data-dir=/tmp/{name} " + 
                    "--name {name} " + 
                    "--initial-advertise-peer-urls http://{ip}:2380 "+
                    "--listen-peer-urls http://{ip}:2380 " + 
                    "--listen-client-urls http://{ip}:2379,http://127.0.0.1:2379 " + 
                    "--advertise-client-urls http://{ip}:2379 " + 
                    "--initial-cluster {cluster} " +
                    "--initial-cluster-token {cluster_token} " +
                    "--initial-cluster-state {cluster_state} " 
                    ).format(
                        name=node_name, 
                        ip=ip, 
                        cluster=cluster, 
                        cluster_state="new", 
                        cluster_token="urop_cluster"
                    )

        print("Start cmd: " + start_cmd)
        print()
        print(docker.cmd(start_cmd))
        restarters.append(lambda:docker.cmd(start_cmd))

    return restarters
