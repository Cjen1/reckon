from threading import Thread as Thread
from time import time as time
from time import sleep as sleep

import argparse
import importlib
from os import listdir
import os

from sys import argv, stdout, stderr

from src.client_runner import run_test 
from src.distributions import register_ops_args
from src.distributions import get_ops_provider
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
register_ops_args(parser)
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
topo_module = importlib.import_module('src.topologies.' + topo)

fail_type = args.failure
fail_args = args.fail_args
print(fail_type, fail_args)
fail_module = importlib.import_module('src.failures.' + fail_type)
fail_setup = fail_module.setup


## A list of benchmark configs with defaults. Change values as appropriate when we have an 
## idea of what values *are* appropriate.
bench_defs = {
        'nclients': 1, 
        'rate': 1,		# upper bound on reqs/sec 
	'duration': 160,	# duration of operation sending in seconds
        'dest': '../results/test.res', 
        'logs': '../logs/test.log', 
        'cpu_quota' : 100,
        'memory_quota' : '4096',
        'memory_unit' : 'megabytes'
        }
bench_args = {}
if args.benchmark_config != "":
    bench_args = dict([arg.split('=') for arg in args.benchmark_config.split(',') ]) 
for key, val in bench_defs.items():
	bench_args.setdefault(key, val)#set as arg or as default value 

print(bench_args)

absolute_path = args.absolute_path

service_name, client_name = system.split("_")

net, cluster, clients, restarters, stoppers = topo_module.setup(service_name, absolute_path, logs=bench_args['logs'], **topo_kwargs) 
failures = fail_setup(net, restarters, stoppers, system.split('_')[0])

hosts = [h for h in net.hosts if h.name[0] == "h"]

if args.d:
    from mininet.cli import CLI
    CLI(net)
else:
    duration = float(bench_args['duration'])
    print("BENCHMARK: " + str(duration))

    ops_provider = get_ops_provider(args)

    print("Benchmark: Waiting for network to settle")
    sleep(10) 
    print("BENCHMARK: Starting Test, "+str((service_name, client_name)))
    run_test(
                bench_args['dest'],
                clients, 
                ops_provider,
                bench_args['rate'],
                bench_args['duration'],
                service_name,
                client_name,
                cluster,
                failures,
            )  

    print("Finished Test")
