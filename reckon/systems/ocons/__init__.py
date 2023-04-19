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

    def get_client(self, args):
        if args.client == str(ClientType.Ocaml) or args.client is None:
            return Ocaml(args)
        else:
            raise Exception("Not supported client type: " + str(args.client))

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

            def start_cmd(tag=tag):
                cmd = " ".join([
                    "nix run ./reckon/systems/ocons/ocons-src --",
                    f"-p {server_port}",
                    f"-q {client_port}",
                    f"-t 0.1",
                    f"--stat 1",
                    self.system_kind,
                    str(hidx),
                    cluster_str,
                ])
                cmd = self.add_stderr_logging(cmd, tag)
                cmd = self.add_stdout_logging(cmd, tag)
                return cmd

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
        f = open(logpath, "r")
        log = f.read().splitlines()
        f.close()

        mterm = -1
        for line in log:
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
