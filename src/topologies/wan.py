from mininet.net import Mininet
from mininet.node import Controller, UserSwitch, IVSSwitch, OVSSwitch
from mininet.log import info, setLogLevel
from mininet.link import TCLink

setLogLevel("info")


class WanTopologyProvider:
    def __init__(
        self,
        number_nodes,
        link_latency,
    ):
        self.number_nodes = number_nodes
        self.link_latency = link_latency
        self.net = None

        self.switch_num = 0
        self.host_num = 0
        self.client_num = 0

    def add_switch(self):
        name = "s%s" % str(self.switch_num + 1)
        self.switch_num += 1
        return self.net.addSwitch(name)

    def add_host(self):
        name = "h%s" % str(self.host_num + 1)
        self.host_num += 1
        return self.net.addHost(name)

    def add_client(self):
        name = "mc%s" % str(self.client_num + 1)
        self.client_num += 1
        return self.net.addHost(name)

    def setup(self):
        self.net = Mininet(controller=Controller, link=TCLink)
        self.net.addController("c0")
        sw = self.add_switch()

        def create_cluster():
            host = self.add_host()
            client = self.add_client()
            sw = self.add_switch()

            self.net.addLink(sw, host)
            self.net.addLink(sw, client)

            return (host, client, sw)

        clusters = [create_cluster() for _ in range(self.number_nodes)]

        for _, _, swc in clusters:
            self.net.addLink(sw, swc, delay=self.link_latency)

        hosts = [host for host, _, _ in clusters]
        clients = [client for _, client, _ in clusters]

        self.net.start()

        return (self.net, hosts, clients)
