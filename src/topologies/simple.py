from mininet.net import Mininet
from mininet.node import Controller, UserSwitch, IVSSwitch, OVSSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')
import cgroups
import importlib

switch_num = 0
def add_switch(net):
    global switch_num
    res = 's%s' %str(switch_num)
    switch_num += 1
    return net.addSwitch(res)

host_num = 0
def add_host(net):
    global host_num
    res = 'h%s' %str(host_num)
    host_num += 1
    return net.addHost(res)

client_num = 0
def add_client(net):
    global client_num
    res = 'mc%s' %str(client_num)
    client_num += 1
    return net.addHost(res)

def setup(service, current_dir, logs, n='3', nc='10'):
    n = int(n)
    nc = int(nc)
    #- Core setup -------

    net = Mininet(controller=Controller)
    info('*** Adding controller\n')
    net.addController('c0')
    
    info('*** Adding switches\n')
    sw = add_switch(net)
    
    info('*** Adding hosts and links\n')
    cluster = [
            add_host(net)
            for _ in range(n)
            ]

    clients = [
            add_client(net)
            for _ in range(nc)
            ]

    for host in cluster:
        net.addLink(host,sw)
    for client in clients:
        net.addLink(client,sw)

    net.start()

    system_setup_func = (
            importlib.import_module(
                "systems.{0}.scripts.setup".format(service)
                )
            ).setup

    kwargs = {'rc':current_dir, 'zk_dist_dir':'{rc}/systems/zookeeper/scripts/zktmp'.format(rc=current_dir)}

    cluster_ips = [host.IP() for host in cluster]

    restarters, cleanup_func = system_setup_func(cluster, cluster_ips, logs=logs, **kwargs)

    return (net, cluster_ips, clients, restarters, cleanup_func)
