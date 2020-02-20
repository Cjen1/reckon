from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from subprocess import call
import importlib

setLogLevel('info')

def follower_down(net, restarters, stoppers, service_name, state):
    hosts = [ net[hostname] for hostname in filter(lambda i: i[0] == 'h', net.keys())]
    ips = [host.IP() for host in hosts]
    print(ips)

    print("FAILURE: Stopping follower")
    leader = importlib.import_module('systems.%s.scripts.find_leader' % service_name).find_leader(hosts, ips)

    follower = [host for host in hosts if not host is leader][0]
    print("FAILURE: killing screen : `screen -X -S %s quit`" % follower.name)

    stoppers[follower.name]()
    state['res'] = restarters[follower.name]

def follower_up(state):
    print("FAILURE: Bringing leader back up")
    state['res']()

def setup(net, restarters, stoppers, service_name):
    state  = {}
    return [
            lambda: follower_down(net, restarters, stoppers, service_name, state),
            lambda: follower_up(state)
            ]
