from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

def failure_setup(net):
    return (lambda:print("fail 1"),
            lambda:print("fail 2"))
