from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from subprocess import call
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
    for host in hosts:
        try:
            cmd = "ETCDCTL_API=3 etcdctl endpoint status --cluster"
            resp = host.cmd(cmd)
            leader_ip = parse_resp(resp)
            leader = hosts[ips.index(leader_ip)]
            print("FAILURE: killing leader: "+leader_ip)
            return leader
        except:
            pass

leader = None
res = None
def leader_down(net, restarters):
    hosts = [ net[hostname] for hostname in filter(lambda i: i[0] == 'd', net.keys())]
    ips = [host.IP() for host in hosts]
    print(ips)

    global leader
    global res
    print("FAILURE: Stopping Leader")
    leader = find_leader(hosts, ips)
    res = restarters[hosts.index(leader)]
    call('docker kill {0}'.format('mn.'+leader.name).split(' '))

def leader_up():
    global leader
    global res
    print("FAILURE: Bringing leader back up")
    call('docker start {0}'.format('mn.'+leader.name).split(' '))
    res()
    leader, res = None, None

def setup(net, restarters):
    return [
            lambda: leader_down(net, restarters),
            lambda: leader_up()
            ]
