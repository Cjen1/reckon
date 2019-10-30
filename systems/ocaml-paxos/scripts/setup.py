from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from sys import stdout

import os

def stop(hosts, cgrps):
    for host in hosts:
        for pid in cgrps[host].pids:
            host.cmd("kill {pid}".format(pid=pid))
    hosts[0].cmd('screen -wipe')

def contain_in_cgroup(cg):
    pid = os.getpid()
    cg.add(pid)


def setup(hosts, ips, cgrps, **kwargs):

    endpoints = "".join(ip + "," for ip in ips)[:-1]

    restarters = []

    acceptor_p1 = "5000"
    acceptor_p2 = "5001"

    client_port = "5002"
    decision_port = "5003"

    replica_req_port = "5004"

    acceptor_uris_p1 = "".join(
            ip + ':' +  acceptor_p1 + ","
            for ip in ips 
            )[:-1]

    acceptor_uris_p2 = "".join(
            ip + ':' + acceptor_p2 + ","
            for ip in ips 
            )[:-1]

    replica_decision_uris = "".join(
            ip + ':' + decision_port + ","
            for ip in ips 
            )[:-1]

    leader_uris = "".join(
            ip + ':' + replica_req_port + ","
            for ip in ips
            )[:-1]
    
    local = "0.0.0.0"

    print(hosts)
    print(ips)

    print(ips)

    restart_commands = [[] for host in hosts]

    client_request_uris = "".join(
            ip + ':' + client_port + ","
            for ip in ips
            )[:-1]
    print(client_request_uris)

    def run(cmd, tag,host):
        #print("getting env")
        #print(host.cmd("env"))
        cmd = "screen -dmS {tag} bash -c \"{command} 2>&1 | tee logs_{tag}\"".format(tag=tag,command=cmd)
        restart_commands[i].append(cmd)
        host.popen(cmd, preexec_fn=lambda:contain_in_cgroup(cgrps[host]), shell=True, stdout=stdout)

    #acceptor startup
    for i, host in enumerate(hosts):
        data_dir = "utils/data/ocaml-paxos-"+str(i)
        cmdp = "screen -dmS op_acceptor_{name} bash".format(name=host.name)
        cmdt = "systems/ocaml-paxos/bin/ocaml-paxos-acceptor {p1} {p2} {data_dir} {local}".format(
                name = host.name,
                p1 = acceptor_p1,
                p2 = acceptor_p2,
                data_dir = data_dir,
                local = local
                )
        cmd = cmdt
        tag = "op_acceptor_" + host.name
        print("Starting acceptor with:")
        print(cmd)
        run(cmd,tag,host)

    #Replica setup
    for i, host in enumerate(hosts):
        cmdp = "screen -dmS op_replica_{name} bash".format(name=host.name)
        #cmdt = "screen -dmS op_replica_{name} systems/ocaml-paxos/bin/ocaml-paxos-replica {lus} {cp} {dp} {local}".format(
        cmdt = "systems/ocaml-paxos/bin/ocaml-paxos-replica {lus} {cp} {dp} {local}".format(
                name = host.name,
                lus = leader_uris,
                cp = client_port,
                dp = decision_port,
                local = local
                )
        cmd = cmdt
        tag = "op_replica_" + host.name
        print("Starting replica with:")
        print(cmd)
        run(cmd,tag,host)

    #Leader setup
    for i, host in enumerate([hosts[0]]):
        cmdp = "screen -dmS op_leader_{name} bash".format(name=host.name)
        cmdt = "systems/ocaml-paxos/bin/ocaml-paxos-leader {aup1} {aup2} {ruds} {rrp} {local}".format(
                name = host.name,
                aup1 = acceptor_uris_p1,
                aup2 = acceptor_uris_p2,
                ruds = replica_decision_uris,
                rrp = replica_req_port,
                local = local
                )
        cmd = cmdt
        tag = "op_leader_" + host.name
        print("Starting leader with:")
        print(cmd)
        run(cmd,tag,host)



    for cmds in restart_commands:
        def restarter():
            for (cmd, host) in cmds:
                run(cmd, "restarter", host)
        restarters.append(restarter)



    return restarters, (lambda: stop(hosts, cgrps))
