from subprocess import call
from sys import argv
import argparse
import socket
import requests
import etcd

def kill(host):
    call (["ssh", host, "docker stop etcd"])

def killLeader(cluster):
    cluster_arg = tuple([(host, 2379) for host in cluster])
    client = etcd.Client(host=cluster_arg, allow_reconnect=True)

    url = client.leader['peerURLs'][0]
    print(url)
    url = url.partition('://')[-1]
    print(url)
    leader = url[:url.index(':')]
    print(leader)

    print("Killing leader: " +leader)

    kill(leader)

parser = argparse.ArgumentParser(description='Stops the either a given server or the leader of a cluster')
parser.add_argument('--hosts')
parser.add_argument('--leader', '-l', action='store_true')
args = parser.parse_args()

hosts = args.hosts.split(',')
if args.leader:
    killLeader(hosts)
else:
    kill(hosts[0])
