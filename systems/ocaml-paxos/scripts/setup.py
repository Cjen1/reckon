from sys import stdout

from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel

import os

def tag(host):
    return "op_"+host.name

def setup(hosts, cgrps, logs, **kwargs):

    restarters = []

    print(hosts)
    print([host.IP() for host in hosts])

    def run(cmd, tag, host):
        cmd = "screen -dmS {tag} bash -c \"{command} 2>&1 | tee logs/{logs}_{tag}\"".format(tag=tag,command=cmd, logs=logs)
        host.popen(cmd, shell=True, stdout=stdout)
        return cmd

    client_port = "2379"
    system_port = "2380"

    cluster = "".join(tag(host) + "="+host.IP()+":" + system_port + "," for i, host in
            enumerate(hosts)
                )[:-1]

    for host in hosts:
        start_cmd = (
                    "systems/ocaml-paxos/bin/ocaml-paxos " +
                    "{client_port}" +
                    "{wal} " + 
                    "{node_name} " + 
                    "{endpoints} " +
                    "{election_timeout} "
                    ).format(
                            client_port = client_port,
                            wal = "/data/{tag}",
                            node_name = tag(host),
                            endpoints = cluster,
                            election_timeout = "0.5"
                            )

        start_cmd = run(start_cmd, tag(host), host)
        print("Start cmd: " + start_cmd)
        print()
        restarters.append(lambda:run(start_cmd, tag(host), host))

    return restarters, (lambda: ())
