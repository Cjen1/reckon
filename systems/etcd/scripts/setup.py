from sys import stdout

from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel

import os

def tag(host):
    return "etcd_"+host.name

def setup(hosts, cgrps, logs, **kwargs):
    cluster = "".join(tag(host) + "=http://"+host.IP()+":2380," for i, host in 
            enumerate(hosts)
                )[:-1]

    restarters = []

    print(hosts)
    print([host.IP() for host in hosts])

    def run(cmd, tag, host):
        cmd = "screen -dmS {tag} bash -c \"{command} 2>&1 | tee logs/{logs}_{tag}\"".format(tag=tag,command=cmd, logs=logs)
        host.popen(cmd, shell=True, stdout=stdout)
        return cmd

    for host in hosts:
        start_cmd = (
                    "systems/etcd/bin/etcd " +
                    "--data-dir=/data/{tag} " + 
                    "--name {tag} " + 
                    "--initial-advertise-peer-urls http://{ip}:2380 "+
                    "--listen-peer-urls http://{ip}:2380 " + 
                    "--listen-client-urls http://0.0.0.0:2379 " + 
                    "--advertise-client-urls http://{ip}:2379 " + 
                    "--initial-cluster {cluster} " +
                    "--initial-cluster-token {cluster_token} " +
                    "--initial-cluster-state {cluster_state} " +
                    "--heartbeat-interval=100 " +
                    "--election-timeout=500"
                    ).format(
                        tag=tag(host),
                        ip=host.IP(), 
                        cluster=cluster, 
                        cluster_state="new", 
                        cluster_token="urop_cluster"
                    )

        start_cmd = run(start_cmd, tag(host), host)
        print("Start cmd: " + start_cmd)
        print()
        restarters.append(lambda:run(start_cmd, tag(host), host))

    return restarters, (lambda: ())
