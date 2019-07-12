from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

def ip_from_int(i):
    return '10.{0:d}.{1:d}.{2:d}'.format(i/(2**16),(i%(2**16))/(2**8),i%(2**8))

def setup(dimage, n=3):
    net = Containernet(controller=Controller)
    info('*** Adding controller\n')
    net.addController('c0')
    
    info('*** Adding switches\n')
    s1 = net.addSwitch('s1')
    
    info('*** Adding docker containers and adding links\n')
    ips = [ip_from_int(i+2) for i in range(n)]
    dockers = [net.addDocker('d' + str(i), ip=ips[i], dimage=dimage) for i in range(n)]

    for d in dockers:
        net.addLink(d,s1)


    return (net, s1, dockers, ips)
