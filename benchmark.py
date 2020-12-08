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
from systems import register_system_args, get_system
from failures import register_failure_args, get_failure_provider
#------- Parse arguments --------------------------
parser = argparse.ArgumentParser(description='Runs a benchmark of a local fault tolerant datastore')

register_system_args(parser)
parser.add_argument(
        'topology',
        help='The topology of the network under test')
parser.add_argument(
        '--topo_args',
        help='Configuration settings for the topology',
        default='')
register_ops_args(parser)
register_failure_args(parser)
parser.add_argument(
        '--benchmark_config',
        default="",
        help='A comma separated list of benchmark parameters, eg. rate=500,duration=10.')
parser.add_argument(
        '-d',
        action='store_true',
        help='Debug mode, sets up mininet, then waits in Mininet.CLI')

args = parser.parse_args()

system = get_system(args)

topo = args.topology
topo_kwargs = dict([arg.split('=') for arg in args.topo_args.split(',')]) if args.topo_args != "" else {}
print(topo, topo_kwargs)
topo_module = importlib.import_module('src.topologies.' + topo)

failure_provider = get_failure_provider(args)

## A list of benchmark configs with defaults. Change values as appropriate when we have an 
## idea of what values *are* appropriate.
bench_defs = {
        'rate': 1,		# upper bound on reqs/sec 
	'duration': 160,	# duration of operation sending in seconds
        'test_results_location': 'test.res', 
        }
bench_args = {}
if args.benchmark_config != "":
    bench_args = dict([arg.split('=') for arg in args.benchmark_config.split(',') ]) 
for key, val in bench_defs.items():
	bench_args.setdefault(key, val)#set as arg or as default value 

print(bench_args)

net, cluster, clients = topo_module.setup(**topo_kwargs) 

restarters, stoppers = system.start_nodes(cluster)
if args.d:
    from mininet.cli import CLI
    CLI(net)
else:
    duration = float(bench_args['duration'])
    print("BENCHMARK: " + str(duration))

    ops_provider = get_ops_provider(args)
    failures = fail_setup(net, restarters, stoppers, system)

    print("BENCHMARK: Starting Test")
    run_test(
                bench_args['test_results_location'],
                clients, 
                ops_provider,
                bench_args['rate'],
                bench_args['duration'],
                system,
                cluster,
                failures,
            )  

    print("Finished Test")
