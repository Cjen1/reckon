from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from sys import stdout

import os
from time import sleep

def stop(hosts, cgrps):
    for host in hosts:
        for pid in cgrps[host].pids:
            host.cmd("kill {pid}".format(pid=pid))
    hosts[0].cmd('screen -wipe')

def contain_in_cgroup(cg):
    pid = os.getpid()
    cg.add(pid)


def setup(hosts, ips, cgrps, logs, **kwargs):

    restarters = []

    restart_commands = [[] for host in hosts]

    def run(cmd, tag, host):
        cmd = "screen -dmS {tag} bash -c \"{command} 2>&1 | tee {logs}_{tag}\"".format(tag=tag, logs=logs, command=cmd)
        print("running with")
        print(cmd)
        host.popen(cmd, preexec_fn=lambda:contain_in_cgroup(cgrps[host]), shell=True, stdout=stdout)
        return cmd

    def run_t(host):
        cmd = "screen -dmS {tag} bash".format(tag=tag)
        host.popen(cmd, preexec_fn=lambda:contain_in_cgroup(cgrps[host]), shell=True, stdout=stdout)

    tags = ["op_" + host.name for host in hosts]

    system_port = "5000"
    client_port = "5001"
    endpoints = "".join(
            "{tag}={ip}:{system_port},".format(tag=tag,ip=ip,system_port=system_port)
            for tag,ip in zip(tags, ips)
            )[:-1]

    for i, (host, tag, ip) in enumerate(zip(hosts,tags,ips)):
        log_location = "utils/data/"+tag
        cmd = "./systems/ocaml-paxos/bin/ocaml-paxos {client_port} {log_location} {node_id} {endpoints} 60".format(
                client_port = client_port,
                log_location=log_location,
                node_id=tag,
                endpoints=endpoints,
                )
        print("Starting ocaml-paxos with:")
        print(cmd)
        #run_t(host)
        cmd = run(cmd,tag,host)
        sleep(0.5)
        restart_commands[i].append(cmd)

    for cmds in restart_commands:
        def restarter():
            for (cmd, host) in cmds:
                run(cmd, "restarter", host)
        restarters.append(restarter)



    return restarters, (lambda: stop(hosts, cgrps))
