from sys import stdout

from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel

import os

def stop(hosts, cgrps):
    for host in hosts:
        for pid in cgrps[host].pids:
            host.cmd("kill {pid}".format(pid=pid))
    hosts[0].cmd('screen -wipe')

def contain_in_cgroup(cg):
    """
    pid = os.getpid()
    cg.add(pid)
    """
    pass


def setup(hosts, ips, cgrps, **kwargs):
    node_names = ["etcd_" + host.name for host in hosts]
    cluster = "".join(name + "=http://"+ip+":2380," for i, (ip, name) in 
            enumerate(
                zip(
                    ips,
                    node_names)
                ))[:-1]

    restarters = []

    print(hosts)
    print(ips)
    for i, (host, ip, node_name) in enumerate(zip(hosts, ips, node_names)):
        start_cmd = (
                    "screen -d -S etcd_{name} -m etcd " +
                    "--data-dir=utils/data/etcd-{node_name} " + 
                    "--name {node_name} " + 
                    "--initial-advertise-peer-urls http://{ip}:2380 "+
                    "--listen-peer-urls http://{ip}:2380 " + 
                    "--listen-client-urls http://{ip}:2379,http://127.0.0.1:2379 " + 
                    "--advertise-client-urls http://{ip}:2379 " + 
                    "--initial-cluster {cluster} " +
                    "--initial-cluster-token {cluster_token} " +
                    "--initial-cluster-state {cluster_state} " 
                    ).format(
                        node_name=node_name, 
                        name=host.name,
                        ip=ip, 
                        cluster=cluster, 
                        cluster_state="new", 
                        cluster_token="urop_cluster"
                    )

        print("Start cmd: " + start_cmd)
        print()
        host.popen(start_cmd, preexec_fn=lambda:contain_in_cgroup(cgrps[host]), stdout=stdout)
        restarters.append(lambda:host.popen(start_cmd, preexec_fn=lambda:contain_in_cgroup(cgrps[host]), stdout=stdout))

    return restarters, (lambda: stop(hosts, cgrps))
