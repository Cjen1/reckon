from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel

import os

def stop(hosts, cgrps):
    for hosts in hosts:
        for pid in cgrps[host]:
            host.cmd("kill {pid}".format(pid))
        hosts[0].cmd("screen -wipe")



def contain_in_cgroup(cg):
    pid = os.getpid()
    cg.add(pid)


def setup(dockers, ips, cgrps, **kwargs):
    endpoints = "".join(ip + "," for ip in ips)[:-1]

    restarters = []

    print(dockers)
    print(ips)
    for i, (docker) in enumerate(dockers):
        data_dir = "utils/data/"+str(i)
        start_cmds = [
                    "screen -d -S op_acceptor_{name} -m ocaml-paxos-acceptor {data_dir}".format(
                        name = docker.name,
                        data_dir = data_dir + "_acceptor",
                        ),
                    "screen -d -S op_leader_{name} -m ocaml-paxos-leader {endpoints} {data_dir}".format(
                        name = docker.name,
                        endpoints = endpoints,
                        data_dir = data_dir + "_leader",
                        ),
                    "screen -d -S op_replica_{name} -m ocaml-paxos-replica {endpoints} {data_dir}".format(
                        name = docker.name,
                        endpoints = endpoints,
                        data_dir = data_dir + "_replica",
                        )
                    ]

        def restarter():
            for cmd in start_cmds:
                print(docker.popen(cmd, preexec_fn=lambda:contain_in_cgroup(cgrps[docker])))

        restarters.append(restarter)

        print("Start cmd: ")
        print(start_cmds)
        restarter()


    return restarters, (lambda: stop(dockers))
