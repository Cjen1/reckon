from sys import stdout
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel

import os

def stop(hosts, cgrps):
    for host in hosts:
        for pid in cgrps[host].pids:
            docker.cmd("kill {pid}".format(pid=pid))
    hosts[0].cmd('screen -wipe')

def contain_in_cgroup(cg):
    """
    pid = os.getpid()
    cg.add(pid)
    """
    pass


def setup(dockers, ips, cgrps, **kwargs):
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
        docker.popen(start_cmd, preexec_fn=lambda:contain_in_cgroup(cgrps[docker]), stdout=stdout)
        restarters.append(lambda:docker.popen(start_cmd, preexec_fn=lambda:contain_in_cgroup(cgrps[docker]), stdout=stdout))

    return restarters, (lambda: stop(dockers, cgrps))
