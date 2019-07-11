from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

def parse_resp(resp):
    enpoint_statuses = resp.split('\n')
    leader = ''
    for endpoint in endpoint_statuses:
        endpoint_ip = endpoint.split(',')[0].split('://')[-1].split(':')[0]
        if(endpoint.split(',')[4] == 'true'):
            leader = endpoint_ip
            break
    return leader

def setup(net):
    hosts = [ net[hostname] for hostname in filter(lambda i: i[0] == 'd', net.keys())]
    ips = [host.IP() for host in hosts]

    cmd = "ETCDCTL=3 etcdctl endpoint status --cluster"
    leader_ip = parse_resp(hosts[0].cmd(cmd))
    leader = hosts[ips.index(leader_ip)]
    leader_name = leader.name

    return [
            lambda: net.configLinkStatus('s1', leader_name, 'down'),
            lambda: net.configLinkStatus('s1', leader_name, 'up')
            ]
