import Queue
from Queue import Queue as queue
from threading import Thread as Thread
from time import time as time

import argparse
import importlib
from os import listdir

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
        'distribution',
        help='The distribution to generate operations from')
parser.add_argument(
        'dist_args',
        help='settings for the distribution. eg. size=5,mean=10')
parser.add_argument(# May swap this out for optional arguments with sensible defaults
        'service_setup',
        help='The setup of the service. eg. nservers=10')
parser.add_argument(
        'systems',
        help='A comma separated list of systems to test. eg. etcd_go,etcd_cli,zookeeper_java to test the go and cli clients for etcd as well as the java client for zookeeper.')
parser.add_argument(
	'cluster',
	help='A comma-separated list of servers on which the system is running.')
parser.add_argument(
        'benchmark_config',
        help='A comma separated list of benchmark parameters, eg. nclients=20,rate=500.')

args = parser.parse_args()

## A list of benchmark configs with defaults. Change values as appropriate when we have an 
## idea of what values *are* appropriate.

bench_defs = [('nclients', 10), ('rate', 100)] 
# rate is the upper bound on the number of requests per second

distribution = args.distribution
dist_args = args.dist_args.split(',')
dist_args = dict([arg.split('=') for arg in dist_args])
op_gen_module = importlib.import_module('distributions.' + distribution)
op_prereq = op_gen_module.generate_prereqs(**dist_args)		
op_gen_gen = lambda : op_gen_module.generate_ops(**dist_args)		

systems = args.systems.split(',')
service_args = args.service_setup.split(',')
cluster = args.cluster.split(',')
bench_args = args.benchmark_config.split(',')
service_args = dict([arg.split('=') for arg in service_args])
bench_args = dict([arg.split('=') for arg in bench_args])

# Make sure that benchmark is fully configured:
for arg, val in bench_defs:
	bench_args.setdefault(arg, val) # If arg is not already presents sets to default value

bench_args = {k : int(v) for k,v in bench_args.items()}

def producer(op_gen, op_buf, rate):
	opid = 0
	start = time()
	while(True):
		while time() < start + opid * 1.0/float(rate):
			pass
		try:
			op_buf.put_nowait(op_gen(opid))
		except Queue.Full:
			pass
		opid += 1

for system in systems:
	operation_buffer = queue(maxsize=3*rate) # don't waste any memory after 3 seconds of not consuming ops.
	
	op_producer = Thread(target=producer, args=[op_gen_gen, operation_buffer, bench_args['rate']])
	op_producer.setDaemon(True)
	# Not starting yet. Otherwise might build up ops during prereq leading 
	# to overload before benchmark should really begin, which defeats 
	# the purpose of rate throttling. 
	
	operation_bundle = [op_producer, operation_buffer, op_prereq]
	
	tester.run_test(tag=tag(), cluster_hostnames=cluster, op_obj=operation_bundle, num_cli=bench_args['nclients'], sys=system) 
	#TODO: Update just how tagging works. For now always uses default values, sort the other args to run_test
