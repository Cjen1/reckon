from mininet.net import Mininet
from mininet.node import Controller, UserSwitch, IVSSwitch, OVSSwitch
from mininet.log import info, setLogLevel

setLogLevel("info")
import importlib

switch_num = 1


def add_switch(net):
    global switch_num
    res = "s%s" % str(switch_num)
    switch_num += 1
    return net.addSwitch(res)


host_num = 1


def add_host(net):
    global host_num
    res = "h%s" % str(host_num)
    host_num += 1
    return net.addHost(res)


client_num = 1


def add_client(net):
    global client_num
    res = "mc%s" % str(client_num)
    client_num += 1
    return net.addHost(res)


def setup(n="3", nc="10"):
    n = int(n)
    nc = int(nc)
    # - Core setup -------

    net = Mininet(controller=Controller)
    info("*** Adding controller\n")
    net.addController("c0")

    info("*** Adding switches\n")
    sw = add_switch(net)

    info("*** Adding hosts and links\n")
    cluster = [add_host(net) for _ in range(n)]

    clients = [add_client(net) for _ in range(nc)]

    for host in cluster:
        net.addLink(host, sw)
    for client in clients:
        net.addLink(client, sw)

    net.start()

    cluster_ips = [host.IP() for host in cluster]

    return (net, cluster, clients)
