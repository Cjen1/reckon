from enum import Enum
import subprocess
import logging

import reckon.reckon_types as t


class Go(t.AbstractClient):
    client_path = "reckon/systems/etcd/clients/go/client"

    def __init__(self, args):
        self.ncpr = args.new_client_per_request

    def cmd(self, ips, client_id) -> str:
        return "{client_path} --targets={ips} --id={client_id} --ncpr={ncpr}".format(
            client_path=self.client_path,
            ips=",".join(f"http://{ip}:2379" for ip in ips),
            client_id=str(client_id),
            ncpr=self.ncpr,
        )


class GoTracer(Go):
    client_path = "reckon/systems/etcd/clients/go-tracer/client"


class ClientType(Enum):
    Go = "go"
    GoTracer = "go-tracer"

    def __str__(self):
        return self.value


class Etcd(t.AbstractSystem):
    binary_path = "reckon/systems/etcd/bin/etcd"
    additional_flags = ""

    def get_client(self, args):
        if args.client == str(ClientType.Go) or args.client is None:
            return Go(args)
        elif args.client == str(ClientType.GoTracer):
            return GoTracer(args)
        else:
            raise Exception("Not supported client type: " + str(args.client))

    def start_nodes(self, cluster):
        cluster_str = ",".join(
            self.get_node_tag(host) + "=http://" + host.IP() + ":2380"
            for _, host in enumerate(cluster)
        )

        restarters = {}
        stoppers = {}

        for host in cluster:
            tag = self.get_node_tag(host)

            def start_cmd(cluster_state, tag=tag, host=host):
                election_timeout = self.failure_timeout * 1000
                heartbeat_interval = election_timeout / 10

                etcd_cmd = " ".join([
                    self.binary_path,
                    f"--data-dir={self.data_dir}/{tag}",
                    f"--name {tag}",
                    f"--initial-advertise-peer-urls http://{host.IP()}:2380",
                    f"--listen-peer-urls http://{host.IP()}:2380",
                    f"--listen-client-urls http://0.0.0.0:2379",
                    f"--advertise-client-urls http://{host.IP()}:2379",
                    f"--initial-cluster {cluster_str}",
                    f"--initial-cluster-token reckon_cluster",
                    f"--initial-cluster-state {cluster_state}",
                    f"--heartbeat-interval={int(heartbeat_interval)}",
                    f"--election-timeout={int(election_timeout)}",
                    ])
                cmd = self.add_stderr_logging(etcd_cmd, tag + ".log")
                cmd = self.add_stdout_logging(cmd, tag + ".log")
                return cmd

            self.start_screen(host, start_cmd("new"))
            logging.debug("Start cmd: " + start_cmd("new"))

            # We use the default arguemnt to capture the host variable semantically rather than lexically
            stoppers[tag] = lambda host=host: self.kill_screen(host)

            restarters[tag] = lambda host=host, start_cmd=start_cmd: self.start_screen(
                host, start_cmd("existing")
            )

        return restarters, stoppers

    def start_client(self, client, client_id, cluster) -> t.Client:
        logging.debug("starting microclient: " + str(client_id))
        tag = self.get_client_tag(client)

        cmd = self.client_class.cmd([host.IP() for host in cluster], client_id)
        cmd = self.add_stderr_logging(cmd, tag + ".log")

        logging.debug("Starting client with: " + cmd)
        sp = client.popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=True,
            bufsize=4096,
        )
        return t.Client(sp.stdin, sp.stdout, client_id)

    def parse_resp(self, resp):
        logging.debug("--------------------------------------------------")
        logging.debug(resp)
        logging.debug("--------------------------------------------------")
        endpoint_statuses = resp.split("\n")[0:-1]
        for endpoint in endpoint_statuses:
            endpoint_ip = endpoint.split(",")[0].split("://")[-1].split(":")[0]
            if endpoint.split(",")[4].strip() == "true":
                return endpoint_ip

    def get_leader(self, cluster):
        ips = [host.IP() for host in cluster]
        for host in cluster:
            try:
                cmd = "ETCDCTL_API=3 reckon/systems/etcd/bin/etcdctl endpoint status --cluster"
                resp = host.cmd(cmd)
                leader_ip = self.parse_resp(resp)
                leader = cluster[ips.index(leader_ip)]
                return leader
            except:
                pass

    def stat(self, host: t.MininetHost) -> str:
        cmd = "ETCDCTL_API=3 reckon/systems/etcd/bin/etcdctl endpoint metrics"
        resp = host.cmd(cmd)
        assert(resp)
        return resp

class EtcdSBN(Etcd):
    binary_path = "reckon/systems/etcd/etcd/bin/etcd"

class EtcdPreVote(Etcd):
    additional_flags = "--pre-vote=True"

class EtcdPreVoteSBN(EtcdPreVote):
    binary_path = "reckon/systems/etcd/etcd/bin/etcd"
