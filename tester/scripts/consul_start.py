from subprocess import call, check_output
from sys import argv
import argparse
import socket
import requests
import etcd

def recover(host):
    call (["ssh", host, "docker start consul"])

parser = argparse.ArgumentParser(description='Restarts each server in cluster')
parser.add_argument('--cluster', '-c')
args = parser.parse_args()

hosts = args.cluster.split(',')

for host in hosts:
    recover(host)
