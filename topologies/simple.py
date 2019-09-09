from mininet.net import Mininet
from mininet.node import Controller, UserSwitch, IVSSwitch, OVSSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')
import cgroups
import importlib

import utils
from utils import addClient

def ip_from_int(i):
    return '10.{0:d}.{1:d}.{2:d}'.format(i/(2**16),(i%(2**16))/(2**8),i%(2**8))

def setup(service, abs_path, n=3, nc=1):
    n = int(n)
    nc = int(nc)
    #- Core setup -------

    net = Mininet(controller=Controller, switch=OVSSwitch)
    info('*** Adding controller\n')
    net.addController('c0')
    
    info('*** Adding switches\n')
    s1 = net.addSwitch('s1')
    
    info('*** Adding docker containers and adding links\n')
    cluster_ips = [ip_from_int(nc + i+1) for i in range(n)]
    dimage = "cjj39_dks28/"+service
    print("*** Using image: " + dimage)
    # dockers = [
    #         addDocker(
    #             abs_path,
    #             net,
    #             'd' + str(i+1), 
    #             cluster_ips[i], 
    #             dimage
    #             ) 
    #         for i in range(n)
    #         ]

    dockers = [
            net.addHost(
                'h' + str(i + 1),
                ip = cluster_ips[i]
                )
            for i in range(n)
            ]

    for d in dockers:
        net.addLink(d,s1, cls=TCLink, delay='50ms', bw=1, max_queue_size=200)

    microclients = [
                utils.addClient(abs_path, net, service, 'mc%d' % i, ip=ip_from_int(i + 1))
            for i in range(nc) 
            ]

    for mc in microclients:
        net.addLink(mc, s1) 

    net.start()

    system_setup_func = (
            importlib.import_module(
                "systems.{0}.scripts.setup".format(service)
                )
            ).setup

    kwargs = {'rc':abs_path, 'zk_dist_dir':'{rc}/systems/zookeeper/scripts/zktmp'.format(rc=abs_path)}

    cgrps = {h : cgroups.Cgroup(h.name) for h in dockers+microclients}

    restarters, stop_func = system_setup_func(dockers, cluster_ips, cgrps, **kwargs)

    return (net, cluster_ips, microclients, restarters, stop_func, cgrps)
