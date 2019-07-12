from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

def parse_resp(resp):
    endpoint_statuses = resp.split('\n')[0:-1]
    leader = ''
    for endpoint in endpoint_statuses:
        endpoint_ip = endpoint.split(',')[0].split('://')[-1].split(':')[0]
        if(endpoint.split(',')[4].strip() == 'true'):
            leader = endpoint_ip
            break
    return leader

def find_leader(hosts, ips):
    cmd = "ETCDCTL_API=3 etcdctl endpoint status --cluster"
    resp = hosts[0].cmd(cmd)
    leader_ip = parse_resp(resp)
    leader = hosts[ips.index(leader_ip)]
    return leader

leader = None
def leader_down(net):
    hosts = [ net[hostname] for hostname in filter(lambda i: i[0] == 'd', net.keys())]
    ips = [host.IP() for host in hosts]
    print(ips)

    global leader
    print("Stopping Leader")
    leader = find_leader(hosts, ips)
    if leader != None:
        net.configLinkStatus('s1', leader.name, 'down')

def leader_up(net):
    print("Bringing leader back up")
    net.configLinkStatus('s1', leader.name, 'up')

def setup(net):
    return [
            lambda: leader_down(net),
            lambda: leader_up(net)
            ]
