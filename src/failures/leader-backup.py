from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from subprocess import call
import importlib


setLogLevel('info')

leader = None
res = None
def leader_down(net, restarters, service_name):
    hosts = [ net[hostname] for hostname in filter(lambda i: i[0] == 'h', net.keys())]
    ips = [host.IP() for host in hosts]
    print(ips)

    global leader
    global res
    print("FAILURE: Stopping Leader")
    leader = importlib.import_module('systems.%s.scripts.find_leader' % service_name).find_leader(hosts, ips)
    res = restarters[hosts.index(leader)]
    print("FAILURE: killing screen : `screen -X -S %s quit`" % (service_name + "_" + leader.name))
    leader.cmd('screen -X -S %s quit' % (service_name + "_" + leader.name))

def leader_up():
    global leader
    global res
    print("FAILURE: Bringing leader back up")
#    call('docker start {0}'.format('mn.'+leader.name).split(' '))
    res() # Restarts leader
    leader, res = None, None

def setup(net, restarters, service_name, cgrps):
    return [
            lambda: leader_down(net, restarters, service_name),
            lambda: leader_up()
            ]
