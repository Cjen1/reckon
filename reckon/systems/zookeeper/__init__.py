from enum import Enum
import subprocess
import logging

import reckon.reckon_types as t


class Java(t.AbstractClient):
    client_path = "reckon/systems/zookeeper/bins/client.jar"

    def __init__(self, args):
        self.ncpr = args.new_client_per_request

    def cmd(self, ips, client_id) -> str:
        return "java -jar {client_path} {ips} {client_id} {ncpr}".format(
            client_path=self.client_path,
            ips=",".join(f"{ip}:2379" for ip in ips),
            client_id=str(client_id),
            ncpr=self.ncpr,
        )


class JavaTracer(Java):
    client_path = "reckon/systems/etcd/clients/go-tracer/client"


class ClientType(Enum):
    Java = "java"
    JavaTracer = "java-tracer"

    def __str__(self):
        return self.value


class Zookeeper(t.AbstractSystem):
    server_bin = (
        "reckon/systems/zookeeper/bins/apache-zookeeper-3.8.0-bin/bin/zkServer.sh"
    )

    def get_client(self, args):
        if args.client == str(ClientType.Java) or args.client is None:
            return Java(args)
        elif args.client == str(ClientType.JavaTracer):
            return JavaTracer(args)
        else:
            raise Exception("Not supported client type: " + str(args.client))

    def start_nodes(self, cluster):
        restarters = {}
        stoppers = {}

        heartbeat_time = 100

        for i, host in enumerate(cluster):
            i = i + 1
            tag = self.get_node_tag(host)

            # Create config file and pid_file
            clientPort = 2379
            serverPort = 2380
            electionPort = 2381
            tickTime = heartbeat_time  # milliseconds
            initLimit = 1000  # How long should new followers be allowed to wait before being kicked
            syncLimit = 10  # How long before a follower is removed from the cluster and clients are forced to reconnect to another node

            dataDir = f"/data/{tag}"

            cluster_config = "\n".join(
                f"server.{i+1}={node.IP()}:{serverPort}:{electionPort}"
                for i, node in enumerate(cluster)
            )

            config = "\n".join(
                [
                    f"tickTime={tickTime}",
                    f"dataDir={dataDir}",
                    f"clientPort={clientPort}",
                    f"initLimit={int(initLimit)}",
                    f"syncLimit={int(syncLimit)}",
                    cluster_config,
                ]
            )

            subprocess.run(f"mkdir {dataDir}", shell=True).check_returncode()
            subprocess.run(f"echo {i} > {dataDir}/myid", shell=True).check_returncode()

            print(config)

            # Write cfg
            cfg_dir = f"/data/{tag}.cfg"
            subprocess.run(f"mkdir -p {cfg_dir}", shell=True).check_returncode()
            cfg_path = f"{cfg_dir}/zoo.cfg"
            with open(cfg_path, "w") as f:
                f.write(config)
                f.flush()

            zk_cmd = " ".join(
                [
                    f"ZOO_LOG_FILE=/results/logs/{tag}.zklogfile",
                    f"ZOO_LOG_DIR=/results/logs/{tag}.zklogdir",
                    f"{self.server_bin}",
                    f"--config {cfg_dir}",
                    f"start-foreground",
                ]
            )
            zk_cmd = self.add_logging(zk_cmd, tag + ".log")

            self.start_screen(host, zk_cmd)
            print("Start cmd: " + zk_cmd)

            # We use the default arguemnt to capture the host variable semantically rather than lexically
            stoppers[tag] = lambda host=host: self.kill_screen(host)

            restarters[tag] = lambda host=host, zk_cmd=zk_cmd: self.start_screen(
                host, zk_cmd
            )

        return restarters, stoppers

    def start_client(self, client, client_id, cluster) -> t.Client:
        logging.debug("starting microclient: " + str(client_id))
        tag = self.get_client_tag(client)

        cmd = self.client_class.cmd([host.IP() for host in cluster], client_id)
        cmd = self.add_logging(cmd, tag + ".log")

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

    # def parse_resp(self, resp):
    #    logging.debug("--------------------------------------------------")
    #    logging.debug(resp)
    #    logging.debug("--------------------------------------------------")
    #    endpoint_statuses = resp.split("\n")[0:-1]
    #    for endpoint in endpoint_statuses:
    #        endpoint_ip = endpoint.split(",")[0].split("://")[-1].split(":")[0]
    #        if endpoint.split(",")[4].strip() == "true":
    #            return endpoint_ip

    def get_leader(self, cluster):
        # TODO
        pass
        # ips = [host.IP() for host in cluster]
        # for host in cluster:
        #    try:
        #        cmd = "ETCDCTL_API=3 reckon/systems/etcd/bin/etcdctl endpoint status --cluster"
        #        resp = host.cmd(cmd)
        #        leader_ip = self.parse_resp(resp)
        #        leader = cluster[ips.index(leader_ip)]
        #        return leader
        #    except:
        #        pass
