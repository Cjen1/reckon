from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel

def stop(dockers):
    for docker in dockers:
        docker.cmd("screen -X -S etcd_{name} quit".format(name=docker.name))


def setup(dockers, ips, **kwargs):
    node_names = ["etcd_" + docker.name for docker in dockers]
    cluster = "".join(name + "=http://"+ip+":2380," for i, (ip, name) in 
            enumerate(
                zip(
                    ips,
                    node_names)
                ))[:-1]

    restarters = []

    print(dockers)
    print(ips)
    for i, (docker, ip, node_name) in enumerate(zip(dockers, ips, node_names)):
        start_cmd = (
                    "screen -d -S etcd_{name} -m etcd " +
                    "--data-dir=utils/data/etcd-node_name --name {node_name} " + 
                    "--initial-advertise-peer-urls http://{ip}:2380 --listen-peer-urls http://0.0.0.0:2380 " + 
                    "--advertise-client-urls http://{ip}:2379 --listen-client-urls http://0.0.0.0:2379 " + 
                    "--initial-cluster {cluster} " +
                    "--initial-cluster-state {cluster_state} --initial-cluster-token {cluster_token}"

                    #"screen -d -S etcd_{name} -m etcd " +
                    #"--data-dir /tmp/{node_name}" + #utils/data/etcd-{node_name} " + 
                    #"--name={node_name} " + 
                    #"--initial-advertise-peer-urls http://127.0.0.1:2380 "+
                    #"--listen-peer-urls http://127.0.0.1:2380 " + 
                    #"--listen-client-urls http://{ip}:2379,http://127.0.0.1:2379 " + 
                    #"--advertise-client-urls http://{ip}:2379 " + 
                    #"--initial-cluster {cluster} " +
                    #"--initial-cluster-token {cluster_token} " +
                    #"--initial-cluster-state {cluster_state} " 
                    ).format(
                        node_name=node_name, 
                        name=docker.name,
                        ip=ip, 
                        cluster=cluster, 
                        cluster_state="new", 
                        cluster_token="urop_cluster"
                    )

        print("Start cmd: " + start_cmd)
        print()
        print(docker.cmd(start_cmd))
        restarters.append(lambda:docker.cmd(start_cmd))

    return restarters, (lambda: stop(dockers))
