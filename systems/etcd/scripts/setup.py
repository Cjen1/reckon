from sys import stdout

from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from subprocess import call
import shlex

import os

def tag(host):
    return host.name

def kill(host):
    cmd = ("screen -X -S {0} quit").format(host.name)
    print("calling: " + cmd)
    call(shlex.split(cmd))


def setup(hosts, cgrps, logs, **kwargs):
    cluster = "".join(tag(host) + "=http://"+host.IP()+":2380," for i, host in
            enumerate(hosts)
                )[:-1]

    restarters = {}
    stoppers = {}

    print(hosts)
    print([host.IP() for host in hosts])

    def run(cmd, tag, host):
        cmd = "screen -dmS {tag} bash -c \"{command} 2>&1 | tee -a logs/{logs}_{tag}\"".format(tag=tag,command=cmd, logs=logs)
        host.popen(cmd, shell=True, stdout=stdout)
        return cmd

    for host in hosts:
        def start_cmd(cluster_state): 
           return (
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
                        cluster_state=cluster_state, 
                        cluster_token="urop_cluster"
                    )

        run(start_cmd("new"), tag(host), host)
        print("Start cmd: " + start_cmd("new"))

        restarters[tag(host)] = lambda:run(start_cmd("existing"), tag(host), host)
        stoppers[host.name] = shlex.split(("screen -X -S {0} quit").format(host.name))

    return restarters, stoppers
