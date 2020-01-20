
import importlib
from mininet.net import Mininet
from mininet.node import Controller
from mininet.log import info, setLogLevel
setLogLevel('info')

switch_num = 0
def add_switch(net):
    global switch_num
    res = 's%s' %str(switch_num)
    switch_num += 1
    return net.addSwitch(res)

host_num = 0
def add_host(net):
    global host_num
    res = 's%s' %str(host_num)
    host_num += 1
    return net.addHost(res)

client_num = 0
def add_client(net):
    global client_num
    res = 's%s' %str(client_num)
    client_num += 1
    return net.addHost(res)

def setup(service, current_dir, logs, num_clusters='1', nodes_per_cluster='3', clients_per_cluster='20'):
    nodes_per_cluster = int(nodes_per_cluster)
    num_clusters = int(num_clusters)
    clients_per_cluster = int(clients_per_cluster)

    net = Mininet(controller=Controller)

    info('*** Adding controller\n')
    net.addController('c0')

    info('*** Adding switches\n')

    root = add_switch(net)

    node_clusters = [
            [
                add_host(net)
                for _ in range(nodes_per_cluster)
                ]
            for _ in range(num_clusters)
            ]

    client_clusters = [
            [
                add_client(net)
                for _ in range(clients_per_cluster)
                ]
            for _ in range(num_clusters)
            ]

    for node_cluster, client_cluster in zip(node_clusters, client_clusters):
        sw = add_switch(net)

        net.addLink(sw, root)
        for node in node_cluster:
            net.addLink(node, sw)

        csw = add_switch(net)
        net.addLink(csw, sw)
        for client in client_cluster:
            net.addLink(client, csw)

    def flatten(ls):
        return [item for sublist in ls for item in sublist]

    nodes = flatten(node_clusters)
    clients = flatten(client_clusters)

    net.start()

    system_setup_func = (
            importlib.import_module(
                "systems.{0}.scripts.setup".format(service)
                )
            ).setup

    kwargs = {'rc':current_dir, 'zk_dist_dir':'{rc}/systems/zookeeper/scripts/zktmp'.format(rc=current_dir)}

    cluster_ips = [host.IP() for host in nodes]

    restarters, stop_func = system_setup_func(nodes, cluster_ips, logs=logs, **kwargs)

    return (net, cluster_ips, clients, restarters, stop_func)
