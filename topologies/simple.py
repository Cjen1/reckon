from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

def setup(container, failure_setup=None, c n=3, setup_func=None):
    net = Containernet(controller=Controller)
    info('*** Adding controller\n')
    net.addController('c0')
    
    info('*** Adding switches\n')
    s1 = net.addSwitch('s1')
    
    info('*** Adding docker containers and adding links\n')
    ips = ['10.0.{0:d}.{1:d}'.format((i) / 256, (i) % 256) for i in range(n)]
    dockers = [net.addDocker('d' + str(i), ip=ips[i], dimage=container) for i in range(n)]

    for d in dockers:
        net.addLink(d,s1)

    failures = failure_setup(net)
    
    info('*** Starting network\n')
    net.start()
    
    if setup_func != None:
        setup_func(dockers, ips)

    return (net, dockers)
