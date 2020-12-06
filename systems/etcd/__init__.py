from enum import Enum
import subprocess

from systems import AbstractSystem, AbstractClient

class Go(AbstractClient):
    def cmd(ips, client_id, result_address):
        client_path = "systems/etcd/clients/go/client"
        return "{client_path} {ips} {client_id} {result_pipe}".format(
                client_path = client_path,
                ips = args_ips,
                client_id = str(client_id),
                result_pipe = result_address
                )
class ClientType(Enum):
    Go = "go"

    def __str__(self):
        return self.value

class Etcd(AbstractSystem):
    def get_client(args):
        if args.client is ClientType.Go:
            return Go()
        else 
            raise Exception(
                'Not supported client type: ' + args.client
            )

    def start_nodes(self, cluster):
        cluster_str = ",".join(tag(host) + "=http://"+host.IP()+":2380" for i, host in enumerate(hosts))

        restarters = {}
        stoppers = {}
        
        for host in cluster:
            tag = get_node_tag(host)
            def start_cmd(cluster_state): 
               etcd_cmd = (
                        "systems/etcd/bin/etcd " +
                        "--data-dir=/data/{tag} " + 
                        "--name {tag} " + 
                        "--initial-advertise-peer-urls http://{ip}:2380 "+
                        "--listen-peer-urls http://{ip}:2380 " + 
                        "--listen-client-urls http://0.0.0.0:2379 " + 
                        "--advertise-client-urls http://{ip}:2379 " + 
                        "--initial-cluster {cluster} " +
                        "--initial-cluster-token {cluster_token} " +
                        "--initial-cluster-state {cluster_state} " +
                        "--heartbeat-interval=100 " +
                        "--election-timeout=500"
                        ).format(
                            tag=tag(host),
                            ip=host.IP(), 
                            cluster=cluster, 
                            cluster_state=cluster_state, 
                            cluster_token="urop_cluster"
                        )
                return etcd_cmd + "2>&1 > {log}/{tag}.log".format(log=self.log_location,tag=tag)

            self.start_screen(host, start_cmd("new"), tag)
            print("Start cmd: " + start_cmd("new"))

            stop_cmd = shlex.split(("screen -X -S {0} quit").format(tag))
            stoppers[host.name] = lambda:host.cmdPrint(stop_cmd)

            restarters[tag(host)] = lambda:self.start_screen(host, start_cmd("existing"), tag)

        return restarters, stoppers

    def start_client(self, client, client_id, cluster):
        print("starting microclient: " + str(client_id))
        tag = get_client_tag(host)
        result_address = "src/utils/sockets/" + self.get_client_tag(mn_client)

        args_ips = ",".join("http://" + host.IP() + ":2379" for host in cluster)

        if os.path.exists(address):
            os.unlink(address)
        os.mkfifo(address)

        cmd = self.clientClass.cmd(ips, client_id, result_address)
        cmd = "{cmd} 2> {log}/{tag}.err 1> {log}/{tag}.out".format(
                cmd=cmd,
                log=self.log_location,
                tag=tag
                )

        sp = client.popen(cmd, stdin=subprocess.PIPE)

        results=open(address, "r")

        return sp.stdin, results

    def _parse_resp(resp):
        print("--------------------------------------------------")
        print(resp)
        print("--------------------------------------------------")
        endpoint_statuses = resp.split('\n')[0:-1]
        leader = ''
        for endpoint in endpoint_statuses:
            endpoint_ip = endpoint.split(',')[0].split('://')[-1].split(':')[0]
            if(endpoint.split(',')[4].strip() == 'true'):
                return endpoint_ip

    def get_leader(self, cluster):
        ips = [host.IP() for host in cluster]
        for host in cluster:
            try:
                cmd = "ETCDCTL_API=3 systems/etcd/bin/etcdctl endpoint status --cluster"
                resp = host.cmd(cmd)
                leader_ip = _parse_resp(resp)
                leader = hosts[ips.index(leader_ip)]
                print("FAILURE: killing leader: "+leader_ip)
                return leader
            except:
                pass
