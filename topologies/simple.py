from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

def ip_from_int(i):
    return '10.{0:d}.{1:d}.{2:d}'.format(i/(2**16),(i%(2**16))/(2**8),i%(2**8))

def setup(service, microclient):
    dimage = 

    #- Core setup -------

    net = Containernet(controller=Controller)
    info('*** Adding controller\n')
    net.addController('c0')
    
    info('*** Adding switches\n')
    s1 = net.addSwitch('s1')
    
    info('*** Adding docker containers and adding links\n')
    cluster_ips = [ip_from_int(i+2) for i in range(n)]
    dockers = [
            net.addDocker(
                'd' + str(i+1), 
                ip    = cluster_ips[i], 
                dimage= "cjj39_dks28/"+service,
                tmpfs = ['/tmpfs_data:size=3G']
                ) 
            for i in range(n)
            ]

    for d in dockers:
        net.addLink(d,s1, cls=TCLink, delay='50ms')

    system_setup_func = (
            importlib.import_module(
                "systems.{0}.scripts.setup".format(service)
                )
            ).setup

    microclient = net.addDocker(
            'microclient', 
            ip = '10.0.0.1',
            dimage='cjj39/script_runner',
            volumes = ['/auto/homes/cjj39/mounted/Resolving-Consensus:/mnt/main:rw']
            )

    net.addLink(microclient, s1) 

    net.start()

    system_setup_func(dockers, cluster_ips)

    return (net, cluster_ips, [microclient])
