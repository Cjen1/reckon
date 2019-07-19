import Queue
from Queue import Queue as queue
from threading import Thread as Thread
from time import time as time
from time import sleep as sleep

import argparse
import importlib
from os import listdir
import os

from sys import argv, stdout, stderr

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
        help='A comma separated list of benchmark parameters, eg. nclients=20,rate=500,duration=10.')

args = parser.parse_args()

systems = args.systems.split(',')

topo = args.topology
topo_kwargs = dict([arg.split('=') for arg in args.topo_args.split(',')]) if args.topo_args != "" else {}
print(topo, topo_kwargs)
topo_module = importlib.import_module('topologies.' + topo)

distribution = args.distribution
dist_args = args.dist_args

fail_type = args.failure
fail_args = args.fail_args
print(fail_type, fail_args)
fail_module = importlib.import_module('failures.' + fail_type)
fail_setup = fail_module.setup


## A list of benchmark configs with defaults. Change values as appropriate when we have an 
## idea of what values *are* appropriate.
bench_defs = {
        'nclients': 1, 
        'rate': 100,		# upper bound on reqs/sec 
	'duration': 10,	# duration of operation sending in seconds
        'dest': '../results/test.res'
        }
bench_args = {}
if args.benchmark_config != "":
    bench_args = dict([arg.split('=') for arg in args.benchmark_config.split(',') ]) 
for key, val in bench_defs.items():
	bench_args.setdefault(key, val)#set as arg or as default value 

for system in systems:
    service, client = system.split("_")

    net, cluster_ips, [microclient], restarters = topo_module.setup(service, client, **topo_kwargs) 
    failures = fail_setup(net, restarters)
    
    duration = float(bench_args['duration'])
    print("BENCHMARK: " + str(duration))

    print("BENCHMARK: Starting Test")
    waiter = microclient.popen(
            [
                'python', '/mnt/main/client.py', 
                system,
                distribution,
                "".join(ip + "," for ip in cluster_ips)[:-1],
                '--dist_args', dist_args,
                '--benchmark_config', "".join(str(k)+"="+str(v)+"," for k,v in bench_args.items())[:-1],
                '--duration', str(bench_args['duration']),
            ], 
            stdout=stdout, stderr=stderr)

    sleepTime = duration / (len(failures) + 1)
    for failure in failures:
        print("BENCHMARK: sleeping for" + str(sleepTime))
        sleep(sleepTime)
        failure()
    print("BENCHMARK: sleeping for" + str(sleepTime))
    sleep(sleepTime)
    waiter.wait() # Wait for child process to finish
    
    print("Finished Test")

    result = microclient.cmd("cat /results.res")

    with open(bench_args['dest'], 'w') as f:
        f.write(result)
    
    net.stop()
