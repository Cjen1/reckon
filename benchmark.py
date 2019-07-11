import Queue
from Queue import Queue as queue
from threading import Thread as Thread
from time import time as time

import argparse
import importlib
from os import listdir
from subprocess import Popen

import utils.tester as tester


#------- Utility functions ------------------------
default_reads    = 0.9
default_clients  = 1
default_datasize = 1024

def tag(reads=default_reads, servers=3, clients=default_clients, datasize=default_datasize):
	r = int(reads*100)
	return str(r).zfill(3) + "R_" + str(servers) + "S_" + str(clients).zfill(3) + "C_" + str(datasize).zfill(7) + "B"



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
topo_module = importlib.import_module('topologies.' + distribution)

distribution = args.distribution
dist_args = args.dist_args

failure_type = args.failure
failure_args = args.fail_args
fail_module = importlib.import_module('failures.' + failure_type)
fail_setup = fail_module.setup


## A list of benchmark configs with defaults. Change values as appropriate when we have an 
## idea of what values *are* appropriate.
bench_defs = {
        'nclients': 10, 
        'rate': 100,		# upper bound on reqs/sec 
	'failure_interval': 10	# duration of operation sending in seconds
        }
bench_args = dict(
	[arg.split('=') for arg in args.benchmark_config.split(',') ]
	)
for arg, val in bench_defs:
	bench_args.setdefault(arg, val)#set as arg or as default value 

tester_args_b = []
for opt in ['--distribution', '--dist_args', '--benchmark_config']
    try:
        i = argv.index(opt)
        tester_args_b.append(opt, argv[i+1])
    except ValueError:
        pass

for system in systems:
    service, client = system.split("_")

    system_setup_func = (
            importlib.import_module(
                "systems.{0}.scripts.setup".format(service)
                )
            ).setup

    dimage = "cjj39_dks28/"+service
    client_dimage = "cjj39_dks28/{0}_{1}".format(service,client)

    net, ips, failures = topo_module.setup(dimage, client_dimage, failure_setup=fail_setup, setup_func=**dist_args) 

    #add client

    net.start()
    #start test on client
    #wait until right % through test before running failure functions
    duration = (len(failures) + 1) * failure_interval
    
    Popen(['python', 'utils/tester.py'] + tester_args_b + ['--system', system, '--duration', duration])
    
    for failure in failures:
        time.sleep(bench_args['failure_interval'])
        failure()
    

