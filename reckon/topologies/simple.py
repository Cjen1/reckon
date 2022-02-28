from mininet.net import Mininet
from mininet.node import Controller, Host
from mininet.log import setLogLevel

import reckon.reckon_types as t

setLogLevel("info")


class SimpleTopologyProvider(t.AbstractTopologyGenerator):
    def __init__(self, number_nodes, number_clients):
        self.number_nodes = number_nodes
        self.number_clients = number_clients

        self.switch_num = 0
        self.host_num = 0
        self.client_num = 0

    def add_switch(self):
        name = "s%s" % str(self.switch_num + 1)
        self.switch_num += 1
        return self.net.addSwitch(name)

    def add_host(self) -> Host:
        name = "h%s" % str(self.host_num + 1)
        self.host_num += 1
        return self.net.addHost(name)

    def add_client(self) -> Host:
        name = "mc%s" % str(self.client_num + 1)
        self.client_num += 1
        return self.net.addHost(name)

    def setup(self):
        self.net = Mininet(controller=Controller)
        self.net.addController("c0")
        sw = self.add_switch()

        hosts = [self.add_host() for _ in range(self.number_nodes)]
        clients = [self.add_client() for _ in range(self.number_clients)]

        for host in hosts + clients:
            self.net.addLink(host, sw)

        self.net.start()

        return (self.net, hosts, clients)
