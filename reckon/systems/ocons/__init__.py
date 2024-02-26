from enum import Enum
import subprocess
import logging

import reckon.reckon_types as t
import re

client_port = 5000
server_port = 5001

class Ocaml(t.AbstractClient):
    def __init__(self, _):
        pass

    def cmd(self, ips, client_id) -> str:
        client_path = "./reckon/systems/ocons/clients"
        ips = ",".join(f"{ip}:{client_port}" for ip in ips)
        return f"nix run {client_path} -- {client_id} {ips}"

class ClientType(Enum):
    Ocaml = "ocaml"

    def __str__(self):
        return self.value


class Ocons(t.AbstractSystem):
    system_kind = "paxos"

    election_timeout = 10

    def get_client(self, args):
        if args.client == str(ClientType.Ocaml) or args.client is None:
            return Ocaml(args)
        else:
            raise Exception("Not supported client type: " + str(args.client))

    tick_period = 0.01

    def get_election_timeout(self):
        return int(float(self.failure_timeout) / self.tick_period)

    def start_cmd(self, tag, nid, cluster):
        cmd = " ".join([
            "nix run ./reckon/systems/ocons/ocons-src --",
            f"-p {server_port}",
            f"-q {client_port}",
            f"-t {self.tick_period}",
            f"--election-timeout {self.get_election_timeout()}",
            f"--rand-start 1",
            #f"--stat=1",
            self.system_kind,
            str(nid),
            cluster,
        ])
        cmd = self.add_stderr_logging(cmd, tag)
        cmd = self.add_stdout_logging(cmd, tag)
        return cmd


    def start_nodes(self, cluster):
        cluster_dict = dict([
            (i, host)
            for i, host in enumerate(cluster)
        ])

        cluster_str = ",".join(
            f"{i}:{host.IP()}:{server_port}"
            for i,host in cluster_dict.items()
        )

        restarters = {}
        stoppers = {}

        for hidx, host in cluster_dict.items():
            tag = self.get_node_tag(host)

            start_cmd = lambda tag=tag, hidx=hidx, cluster=cluster_str: self.start_cmd(tag, hidx, cluster)

            self.start_screen(host, start_cmd())
            logging.info("Start cmd: " + start_cmd())

            # We use the default arguemnt to capture the host variable semantically rather than lexically
            stoppers[tag] = lambda host=host: self.kill_screen(host)

            restarters[tag] = lambda host=host, start_cmd=start_cmd: self.start_screen(
                host, start_cmd()
            )

        return restarters, stoppers

    def start_client(self, client, client_id, cluster) -> t.Client:
        logging.debug("starting microclient: " + str(client_id))
        tag = self.get_client_tag(client)

        cmd = self.client_class.cmd([host.IP() for host in cluster], client_id)
        cmd = self.add_stderr_logging(cmd, tag)

        logging.info("Starting client with: " + cmd)
        sp = client.popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=True,
            bufsize=4096,
        )
        return t.Client(sp.stdin, sp.stdout, client_id)

    def get_leader_term(self, host):
        logpath =f"{self.log_location}/{self.creation_time}_{self.get_node_tag(host)}.err"
        cmd = f"grep -i 'leader for term' {logpath}"
        log = host.cmd(cmd)

        mterm = -1
        for line in log.splitlines():
            match = re.search('leader for term (\\d+)', line, re.IGNORECASE)
            if match:
                mterm = max(int(match.group(1)), mterm)
        return mterm if mterm != -1 else None

    def get_leader(self, cluster):
        terms = [(host, self.get_leader_term(host)) for host in cluster]
        terms = [(host, term) for host, term in terms if term]
        max_host, max_term = terms[0]
        for (host, term) in terms:
            if term > max_term:
                max_host = host
                max_term = term
        return max_host

    def stat(self, _):
        pass

class OconsPaxos(Ocons):
    system_kind = "paxos"
class OconsRaft(Ocons):
    system_kind = "raft"
class OconsRaftSBN(Ocons):
    system_kind = "raft+sbn"
class OconsRaftPrevote(Ocons):
    system_kind = "prevote-raft"
class OconsRaftPrevoteSBN(Ocons):
    system_kind = "prevote-raft+sbn"

class OConsConspireLeader(Ocons):
    system_kind = "conspire-leader"

    def start_cmd(self, tag, nid, cluster):
        cmd = " ".join([
            "nix run ./reckon/systems/ocons/ocons-src --",
            f"-p {server_port}",
            f"-q {client_port}",
            f"-t {self.tick_period}",
            f"--election-timeout {self.get_election_timeout()}",
            f"--rand-start 1",
            #f"--stat=1",
            self.system_kind,
            str(nid),
            cluster,
        ])
        cmd = self.add_stderr_logging(cmd, tag)
        cmd = self.add_stdout_logging(cmd, tag)
        return cmd

    def get_leader(self, cluster):
        cluster_dict = dict([
            (i, host)
            for i, host in enumerate(cluster)
        ])

        return cluster_dict[min(cluster_dict.keys())]


class OConsConspireDC(Ocons):
    system_kind = "conspire-dc"

    def start_cmd(self, tag, nid, cluster):
        cmd = " ".join([
            "nix run ./reckon/systems/ocons/ocons-src --",
            f"-p {server_port}",
            f"-q {client_port}",
            f"-t {0.001}",
            f"--rand-start 1",
            #f"--stat=1",
            f"--delay {self.delay_interval}",
            self.system_kind,
            str(nid),
            cluster,
        ])
        cmd = self.add_stderr_logging(cmd, tag)
        cmd = self.add_stdout_logging(cmd, tag)
        return cmd


    def min_latency(self, client, cluster):

        def dispatch_latency(h1 : t.MininetHost, h2):
            return h1.popen(
                    f"ping {h2.IP()} -c 5 -i 0.2 -q",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    shell=True,
                    bufsize=4096
                    )
        
        def await_latency(proc):
            proc.wait()
            out = proc.stdout.read()
            pat = "\d+\.\d*/(\d+\.\d*)/\d+\.\d*/\d+\.\d*"
            match = re.search(pat, out.decode())
            if match is not None:
                return float(match.group(1))
            return None

        latencies = {
                host.IP() : dispatch_latency(client, host)
                for host in cluster
                }
        latencies = {
                k : await_latency(v)
                for k,v in latencies.items()
                }
        print(latencies)
        min_latency = latencies[cluster[0].IP()]
        min_ip = cluster[0].IP()
        for ip, latency in latencies.items():
            if latency is None: continue
            if min_latency is None:
                min_ip = ip
                min_latency = latency

            if latency <= min_latency:
                min_ip = ip
                min_latency = latency
        print(f"{min_ip} is closest with {min_latency} from {client.IP()}")
        return min_ip

    def start_client(self, client, client_id, cluster) -> t.Client:
        logging.debug("starting microclient: " + str(client_id))
        tag = self.get_client_tag(client)

        cmd = self.client_class.cmd([self.min_latency(client, cluster)], client_id)
        cmd = self.add_stderr_logging(cmd, tag)

        logging.info("Starting client with: " + cmd)
        sp = client.popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=True,
            bufsize=4096,
        )
        return t.Client(sp.stdin, sp.stdout, client_id)

    def get_leader(self, cluster):
        return cluster[0]

class OConsConspireLeaderDC(OConsConspireLeader):
    system_kind = "conspire-leader-dc"

    tick_period = 0.01

    def start_cmd(self, tag, nid, cluster):
        cmd = " ".join([
            "nix run ./reckon/systems/ocons/ocons-src --",
            f"-p {server_port}",
            f"-q {client_port}",
            f"-t {self.tick_period}",
            f"--election-timeout {self.get_election_timeout()}",
            f"--delay {self.delay_interval}",
            f"--rand-start 1",
            self.system_kind,
            str(nid),
            cluster,
        ])
        cmd = self.add_stderr_logging(cmd, tag)
        cmd = self.add_stdout_logging(cmd, tag)
        return cmd

    def get_leader(self, cluster):
        cluster_dict = dict([
            (i, host)
            for i, host in enumerate(cluster)
        ])

        return cluster_dict[min(cluster_dict.keys())]
