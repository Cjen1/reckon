from enum import Enum
from sys import stdout
import subprocess
import os
import logging

from ..systems_classes import AbstractSystem, AbstractClient


class OCaml(AbstractClient):
    client_path = "systems/ocons/clients/ocaml/client"

    def __init__(self, args):
        pass

    def cmd(self, ips, client_id):
        return "{client_path} {ips} {client_id} -log-level debug".format(
            client_path=self.client_path,
            ips=ips,
            client_id=str(client_id),
        )


class ClientType(Enum):
    OCaml = "ocaml"

    def __str__(self):
        return self.value


CLIENT_PORT = 2379
INTERNAL_PORT = 2380


class OCons(AbstractSystem):
    binary_path = "not-a-real-system"

    def get_client(self, args):
        if args.client == str(ClientType.OCaml):
            return OCaml(args)
        else:
            raise Exception("Not supported client type: " + args.client)

    def start_nodes(self, cluster):
        node_list = ",".join(
            "{id}:{ip}:{port}".format(id=i, ip=node.IP(), port=INTERNAL_PORT)
            for i, node in enumerate(cluster)
        )

        restarters = {}
        stoppers = {}

        for node_id, host in enumerate(cluster):
            tag = self.get_node_tag(host)

            def start_cmd(tag=tag, node_id=node_id):
                ocons_cmd = (
                    "{binary} "
                    + "{node_id} "
                    + "{node_list} "
                    + "{data_dir} "
                    + "{CLIENT_PORT} "
                    + "{INTERNAL_PORT} "
                    + "5 0.1 -s 500"
                ).format(
                    binary=self.binary_path,
                    node_id=node_id,
                    node_list=node_list,
                    data_dir="/data/" + tag,
                    CLIENT_PORT=CLIENT_PORT,
                    INTERNAL_PORT=INTERNAL_PORT,
                )
                return self.add_logging(ocons_cmd, tag + ".log")

            self.start_screen(host, start_cmd())
            logging.debug("Start cmd: " + start_cmd())

            stoppers[tag] = lambda host=host: self.kill_screen(host)

            restarters[tag] = lambda host=host, start_cmd=start_cmd: self.start_screen(
                host, start_cmd()
            )

        return restarters, stoppers

    def start_client(self, client, client_id, cluster):
        logging.debug("starting microclient: " + str(client_id))
        tag = self.get_client_tag(client)

        args_ips = ",".join(
            "{ip}:{port}".format(ip=host.IP(), port=str(CLIENT_PORT))
            for host in cluster
        )

        cmd = self.client_class.cmd(args_ips, client_id)
        cmd = self.add_logging(cmd, tag + ".log", just_stderr=True)

        logging.debug("Starting client with: " + cmd)
        FNULL = open(os.devnull, "w")
        sp = client.popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=FNULL, shell=True
        )

        return sp.stdin, sp.stdout

    def parse_resp(self, resp):
        logging.debug("--------------------------------------------------")
        logging.debug(resp)
        logging.debug("--------------------------------------------------")
        endpoint_statuses = resp.split("\n")[0:-1]
        leader = ""
        for endpoint in endpoint_statuses:
            endpoint_ip = endpoint.split(",")[0].split("://")[-1].split(":")[0]
            if endpoint.split(",")[4].strip() == "true":
                return endpoint_ip

    def get_leader(self, cluster):
        ips = [host.IP() for host in cluster]
        for host in cluster:
            try:
                cmd = "ETCDCTL_API=3 systems/etcd/bin/etcdctl endpoint status --cluster"
                resp = host.cmd(cmd)
                leader_ip = self.parse_resp(resp)
                leader = cluster[ips.index(leader_ip)]
                return leader
            except:
                pass


class OConsPaxos(OCons):
    binary_path = "systems/ocons/bins/ocons-paxos"
