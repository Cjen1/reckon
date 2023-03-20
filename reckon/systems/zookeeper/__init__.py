from enum import Enum
import subprocess
import logging

import reckon.reckon_types as t


class Java(t.AbstractClient):
    client_path = "reckon/systems/zookeeper/bins/client.jar"

    def __init__(self, args):
        self.ncpr = args.new_client_per_request

    def cmd(self, ips, client_id) -> str:
        return "java -jar {client_path} {ips} {client_id} {ncpr} 20".format(
            client_path=self.client_path,
            ips=",".join(f"{ip}:2379" for ip in ips),
            client_id=str(client_id),
            ncpr=self.ncpr,
        )


class ClientType(Enum):
    Java = "java"

    def __str__(self):
        return self.value


class Zookeeper(t.AbstractSystem):
    bin_dir = "reckon/systems/zookeeper/bins/apache-zookeeper-3.5.10-bin"
    electionAlg = 0

    def get_client(self, args):
        if args.client == str(ClientType.Java) or args.client is None:
            return Java(args)
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

            dataDir = f"{self.data_dir}/{tag}"

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
                    f"4lw.commands.whitelist=*",
                    f"snap_count=1000000",
                    f"max_client_connections=5000",
                    f"globalOutstandingLimit=10000",
                    f"electionAlg={self.electionAlg}",
                    cluster_config,
                ]
            )

            subprocess.run(f"mkdir -p {dataDir}", shell=True).check_returncode()
            subprocess.run(f"echo {i} > {dataDir}/myid", shell=True).check_returncode()

            print(config)

            # Write cfg
            cfg_dir = f"{dataDir}/config"
            subprocess.run(f"mkdir -p {cfg_dir}", shell=True).check_returncode()
            # Copy logback config into config directory
            subprocess.run(f"cp {self.bin_dir}/conf/logback.xml {cfg_dir}/logback.xml", shell=True) .check_returncode()

            cfg_path = f"{cfg_dir}/zoo.cfg"
            with open(cfg_path, "w") as f:
                f.write(config)
                f.flush()

            # --config is passed to zkEnv which then sets up the classpath to have cfg within that directory
            cmd = " ".join(
                [
                    f"ZOO_LOG_FILE=/results/logs/{tag}.zklogfile",
                    f"ZOO_LOG_DIR=/results/logs/{tag}.zklogdir",
                    f"JVMFLAGS=\"-Xms10G -Xmx10G \"",
                    f"{self.bin_dir}/bin/zkServer.sh",
                    f"--config {cfg_dir}",
                    f"start-foreground",
                ]
            )

            #qcmd = cmd.translate(str.maketrans({"\\": r"\\", "\"": r"\""})) # Quote all punctuation
            #cmd = f'bash -c "{qcmd}"' # Encapsulate cmd within a bash environment to ensure logging occurs correctly

            cmd = self.add_stderr_logging(cmd, tag + ".log")
            cmd = self.add_stdout_logging(cmd, tag + ".log")

            self.start_screen(host, cmd)
            print("Start cmd: " + cmd)

            # We use the default arguemnt to capture the host variable semantically rather than lexically
            stoppers[tag] = lambda host=host: self.kill_screen(host)

            restarters[tag] = lambda host=host, cmd=cmd: self.start_screen(
                host, cmd
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

    def get_leader(self, cluster):
        for host in cluster:
           try:
               cmd = "echo stat | nc localhost 2379 | grep Mode"
               resp = host.cmd(cmd)
               if "Mode: leader" in resp:
                   return host
           except:
               pass

    def stat(self, host: t.MininetHost) -> str:
        ret = host.cmd("echo stat | nc 127.0.0.1 2379")
        assert(ret)
        return ret

class ZookeeperFLE(Zookeeper):
    electionAlg = 3 # Use FastLeaderElection
