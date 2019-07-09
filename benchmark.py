import argparse
import importlib
from os import listdir

#------- Parse arguments --------------------------
parser = argparse.ArgumentParser(description='Runs a benchmark of a local fault tolerant datastore')

parser.add_argument(
        'distribution',
        help='The distribution to generate operations from')
parser.add_argument(
        '--dist_args',
        help='settings for the distribution. eg. size=5,mean=10')
parser.add_argument(# May swap this out for optional arguments with sensible defaults
        '--setup_setup',
        help='The setup of the setup. eg. nservers=10')
parser.add_argument(
        'systems',
        help='A comma separated list of systems to test. eg. etcd_go,etcd_cli,zookeeper_java to test the go and cli clients for etcd as well as the java client for zookeeper.')
parser.add_argument(
        'failure',
        help='Injects the given failure into the system')
parser.add_argument(
        '-f', '--fail_args',
        help='Arguments to be passed to the failure script.')

args = parser.parse_args()

distribution = args.distribution
dist_args = args.dist_args.split(',')
dist_args = dict([arg.split('=') for arg in dist_args])
op_gen_module = importlib.import_module('distributions.' + distribution)
op_gen_gen = lambda: (op_gen_module.generate_ops(**dist_args))

systems = args.systems.split(',')
setup_args = args.setup_setup.split(',')
setup_args = dict([arg.split('=') for arg in setup_args])

failure_mode = args.failure
fail_args = args.fail_args

#------- Start system -----------------------------
n = 5
networkargs = {}

#TODO: get docker image from system info 


from mininet.net import Containernet
from mininet.topo import Topo 
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel

setLogLevel('info')

class SingleSwitchTopo(Topo):
    def build(self, n=2):
        switch = self.addSwitch('s1')
        for d in range(n):
            dock = self.addDocker( 'd%s' % (d + 1))
            self.addLink( dock, switch, **networkargs)
