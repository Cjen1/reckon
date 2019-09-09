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

from client_runner import run_test 
#------- Parse arguments --------------------------
parser = argparse.ArgumentParser(description='Runs a benchmark of a local fault tolerant datastore')

parser.add_argument(
        'system',
        help='The system under test, with the client to use. eg etcd_go')
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
        default="",
        help='settings for the distribution. eg. size=5,mean=10')
parser.add_argument(
        'failure',
        help='Injects the given failure into the system')
parser.add_argument(
        '--fail_args',
        help='Arguments to be passed to the failure script.')
parser.add_argument(
        '--benchmark_config',
        default="",
        help='A comma separated list of benchmark parameters, eg. rate=500,duration=10.')
parser.add_argument(
        '-d',
        action='store_true',
        help='Debug mode, sets up mininet, then waits in Mininet.CLI')
parser.add_argument(
        'absolute_path',
        help="The absolute path in the host to this folder, required due to docker weirdness and zmq's ipc rules"
        )

args = parser.parse_args()

system = args.system

topo = args.topology
topo_kwargs = dict([arg.split('=') for arg in args.topo_args.split(',')]) if args.topo_args != "" else {}
print(topo, topo_kwargs)
topo_module = importlib.import_module('topologies.' + topo)

distribution = args.distribution
dist_kwargs = dict([arg.split('=') for arg in args.dist_args.split(',')]) if args.dist_args != "" else {}

fail_type = args.failure
fail_args = args.fail_args
print(fail_type, fail_args)
fail_module = importlib.import_module('failures.' + fail_type)
fail_setup = fail_module.setup


## A list of benchmark configs with defaults. Change values as appropriate when we have an 
## idea of what values *are* appropriate.
bench_defs = {
        'nclients': 1, 
        'rate': 1,		# upper bound on reqs/sec 
	'duration': 160,	# duration of operation sending in seconds
        'dest': '../results/test.res'
        }
bench_args = {}
if args.benchmark_config != "":
    bench_args = dict([arg.split('=') for arg in args.benchmark_config.split(',') ]) 
for key, val in bench_defs.items():
	bench_args.setdefault(key, val)#set as arg or as default value 

absolute_path = args.absolute_path

service_name, client_name = system.split("_")

net, cluster_ips, clients, restarters, cleanup = topo_module.setup(service_name, absolute_path, **topo_kwargs) 
failures = fail_setup(net, restarters, system.split('_')[0])

if args.d:
    from mininet.cli import CLI
    CLI(net)
else:
    duration = float(bench_args['duration'])
    print("BENCHMARK: " + str(duration))

    op_gen_module = importlib.import_module('distributions.' + distribution)

    ops = op_gen_module.generate_ops(**dist_kwargs)		
    print("BENCHMARK: Starting Test, "+str((service_name, client_name)))
    tester = Thread(target=run_test, 
            args=[
                bench_args['dest'],
                clients, 
                ops, 
                bench_args['rate'],
                bench_args['duration'],
                service_name,
                client_name,
                cluster_ips
            ])  
    tester.start()

    sleepTime = duration / (len(failures) + 1)
    for failure in (failures+[(lambda*args, **kwargs:None)]):
        print("BENCHMARK: sleeping for" + str(sleepTime))
        sleep(sleepTime)
        failure()

    tester.join()
    print("Finished Test")

from subprocess import call
cleanup()
net.stop()
