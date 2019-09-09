from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel

def stop(dockers):
    for docker in dockers:
        for name_type in ["op_acceptor", "op_leader", "op_replica"]:
            docker.cmd("screen -X -S {name_type}_{name} quit".format(name_type = name_type, name=docker.name))


def setup(dockers, ips, **kwargs):
    endpoints = "".join(ip + "," for ip in ips)[:-1]

    restarters = []

    print(dockers)
    print(ips)
    for i, (docker) in enumerate(dockers):
        start_cmds = [
                    "screen -d -S op_acceptor_{name} -m ocaml-paxos-acceptor {ip}".format(
                        name = docker.name,
                        ip = "127.0.0.1"
                        ),
                    "screen -d -S op_leader_{name} -m ocaml-paxos-leader {ip} {endpoints}".format(
                        name = docker.name,
                        ip = "127.0.0.1",
                        endpoints = endpoints
                        ),
                    "screen -d -S op_replica_{name} -m ocaml-paxos-replica {ip} {endpoints}".format(
                        name = docker.name,
                        ip = "127.0.0.1",
                        endpoints = endpoints
                        )
                    ]
        def restarter():
            for cmd in start_cmds:
                print(docker.cmd(cmd))

        restarters.append(restarter)

        print("Start cmd: ")
        print(start_cmds)
        restarter()


    return restarters, (lambda: stop(dockers))
