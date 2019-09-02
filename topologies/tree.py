from mininet.net import Containernet
from mininet.node import Controller, UserSwitch, IVSSwitch, OVSSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

from math import ceil
import time
import importlib

import utils
from utils import addClient, addDocker

def ip_from_int(i):
    return '10.{0:d}.{1:d}.{2:d}'.format(i/(2**16),(i%(2**16))/(2**8),i%(2**8))

def setup(service, current_dir, n=3, nc=1):
    n = int(n)
    nc = int(nc)
    #- Core setup -------

    net = Containernet(controller=Controller, switch=OVSSwitch)
    info('*** Adding controller\n')
    net.addController('c0')
    
    info('*** Adding switches\n')

    roots = [net.addSwitch('s%s' % str(i)) for i in range(1)] # roots at the center of the tree structure

    # inner ring of switches, connects servers to network
    num_inner_switches = max(n//2, nc//15)
    
    inner_switches = []

    for i in range(num_inner_switches):
        inner_switches.append(net.addSwitch('s%s' % str(i+len(roots))))

    num_outer_switches = int(ceil((nc // num_inner_switches) / 5.))

    outer_switches = {}
    for i, inner in enumerate(inner_switches):
        outer_switches[inner] = [net.addSwitch('s%s' % str(j + num_outer_switches*i+num_inner_switches+ len(roots)+ 1)) for j in range(num_outer_switches)]
    
    info('*** Adding links between switches\n')
    for i,s in enumerate(inner_switches):
        print("Adding link to inner switch")
        net.addLink(s, roots[0], delay='30ms', bw=10, max_queue_size=500)
        for o in outer_switches[s]:
            net.addLink(o, s, delay='20ms')

    info('*** Adding docker containers and adding links\n')
    cluster_ips = [ip_from_int(nc + i+1) for i in range(n)]
    dimage = "cjj39_dks28/"+service
    print("*** Using image: " + dimage)
    """
    dockers = [
            addDocker(
                current_dir,
                net,
                'd' + str(i+1), 
                cluster_ips[i], 
                dimage
                ) 
            for i in range(n)
            ]
    """
    dockers = [
            net.addHost(
                'h' + str(i + 1),
                ip = cluster_ips[i]
                )
            for i in range(n)
            ]

    def mc_coordinates(did):
        cycle = did // num_inner_switches
        return did % num_inner_switches, cycle % num_outer_switches

    for did,d in enumerate(dockers):
        net.addLink(d, inner_switches[did % num_inner_switches], cls=TCLink, delay='10ms', bw=1, max_queue_size=200)

    microclients = [
                utils.addClient(current_dir, net, service, 'mc%d' % i, ip=ip_from_int(i + 1))
            for i in range(nc) 
            ]

    for i,mc in enumerate(microclients):
        inn, out = mc_coordinates(i)
        net.addLink(mc, outer_switches[inner_switches[inn]][out]) 

    net.start()

    system_setup_func = (
            importlib.import_module(
                "systems.{0}.scripts.setup".format(service)
                )
            ).setup

    kwargs = {'rc':current_dir, 'zk_dist_dir':'{rc}/systems/zookeeper/scripts/zktmp'.format(rc=current_dir)}

    restarters, stop_func = system_setup_func(dockers, cluster_ips, **kwargs)
    """  
    for d in dockers:
        d.update_resources(
                cpu_quota=5000,
                cpu_period=100000
                )
    """
    return (net, cluster_ips, microclients, restarters, stop_func)
