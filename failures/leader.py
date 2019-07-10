from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

def parse_resp(resp):
    assert False
    return None

def failure_setup(net):
hosts = [ net[hostname] for hostname in filter(lambda i: i[0] == 'd', net.keys())
        ]
ips = [host.IP() for host in hosts]

    cmd = ""
    leader_ip = parse_resp(hosts[0].cmd(cmd))
    leader = hosts[ips.index(leader_ip)]
    leader_name = leader.name

    return [
            lambda: net.configLinkStatus('s1', leader_name, 'down'),
            lambda: net.configLinkStatus('s1', leader_name, 'up')
            ]
