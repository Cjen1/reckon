import Queue
from Queue import Queue as queue
from threading import Thread as Thread
from time import time as time
from time import sleep as sleep

import argparse
import importlib
from os import listdir
import os

from sys import argv

#------- Parse arguments --------------------------
parser = argparse.ArgumentParser(description='Runs a benchmark of a local fault tolerant datastore')

parser.add_argument(
        'systems',
        help='A comma separated list of systems to test. eg. etcd_go,etcd_cli,zookeeper_java to test the go and cli clients for etcd as well as the java client for zookeeper.')
parser.add_argument(
        'topology',
        help='The topology of the network under test')
parser.add_argument(
        '--topo_args',
        help='Configuration settings for the topology',
        default='')
parser.add_argument(
        'distribution',
        help='The distribution to generate operations from')
parser.add_argument(
        '--dist_args',
        default="None",
        help='settings for the distribution. eg. size=5,mean=10')
parser.add_argument(
        'failure',
        help='Injects the given failure into the system')
parser.add_argument(
        '--fail_args',
        help='Arguments to be passed to the failure script.')
parser.add_argument(
        'benchmark_config',
        help='A comma separated list of benchmark parameters, eg. nclients=20,rate=500,failure_interval=10.')

args = parser.parse_args()

systems = args.systems.split(',')

topo = args.topology
topo_args = args.topo_args
topo_module = importlib.import_module('topologies.' + topo)

distribution = args.distribution
dist_args = args.dist_args

fail_type = args.failure
fail_args = args.fail_args
fail_module = importlib.import_module('failures.' + fail_type)
fail_setup = fail_module.setup


## A list of benchmark configs with defaults. Change values as appropriate when we have an 
## idea of what values *are* appropriate.
bench_defs = {
        'nclients': 1, 
        'rate': 1,		# upper bound on reqs/sec 
	'failure_interval': 120	# duration of operation sending in seconds
        }
bench_args = {} #dict([arg.split('=') for arg in args.benchmark_config.split(',') ])
for arg, val in bench_defs.items():
	bench_args.setdefault(arg, val)#set as arg or as default value 


for system in systems:
    service, client = system.split("_")

    system_setup_func = (
            importlib.import_module(
                "systems.{0}.scripts.setup".format(service)
                )
            ).setup

    dimage = "cjj39_dks28/"+service

    #TODO pass in args...
    net, switch, hosts, ips = topo_module.setup(dimage) 

    # Any setup of clients etc
    if system_setup_func != None:
        print("Configuring containers")
        system_setup_func(hosts, ips)

    failures = fail_setup(net)

    client = net.addDocker(
            'client', 
            ip = '10.0.0.1',
            dimage='cjj39/containernet',
            volumes = ['/auto/homes/cjj39/mounted/Resolving-Consensus:/mnt/main:rw']
            )

    net.addLink(client, switch) 

    net.start()

    # from mininet.cli import CLI
    # CLI(net)

    duration = (len(failures) + 1) * bench_defs['failure_interval']

    print("Starting Test")
    waiter = client.popen([
        'python', '/mnt/main/client.py', 
            system,
            distribution,
            "".join(ip + "," for ip in ips)[:-1],
            '--dist_args', dist_args,
            '--benchmark_config', "".join(str(k)+"="+str(v)+"," for k,v in bench_args.items())[:-1],
            '--duration', str(duration),
                ])
    
    print("BENCHMARK: starting benchmark")
    for failure in failures:
        sleep(bench_args['failure_interval'])
        failure()
    waiter.wait() # Wait for child process to finish
    
    print("Finished Test")

    result = client.cmd("cat /results.res")

    with open('../results/firstTest.res', 'w') as f:
        f.write(result)
    
    net.stop()

