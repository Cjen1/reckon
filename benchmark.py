import argparse
import importlib
from os import listdir

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

args = parser.parse_args()

distribution = args.distribution
dist_args = args.dist_args.split(',')
dist_args = dict([arg.split('=') for arg in dist_args])
op_gen_module = importlib.import_module('distributions.' + distribution)
op_gen_gen = lambda (): (op_gen_module.generate_ops(**dist_args))

systems = args.systems.split(',')
service_args = args.service_setup.split(',')
service_args = dict([arg.split('=') for arg in service_args])
