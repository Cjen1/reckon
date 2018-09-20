from subprocess import call
from sys import argv
import argparse
import socket
import requests
import etcd

def kill(host):
    call (["ssh", host, "screen -X -S etcd_background quit"])

def getLeader(cluster):
    cluster_arg = tuple([(host, 2379) for host in cluster])
    client = etcd.Client(host=cluster_arg, allow_reconnect=True)
    url = client.leader['peerURLs'][0]
    url = url.partition('://')[-1]
    leader = url[:url.index(':')]
    return leader


def killLeader(cluster):
    leader = getLeader(cluster)
    print("Killing leader: " +leader)
    kill(leader)

parser = argparse.ArgumentParser(description='Stops the either a given server or the leader of a cluster')
parser.add_argument('--cluster', '-c')
parser.add_argument('--leader', '-l', action='store_true')
args = parser.parse_args()

hosts = args.cluster.split(',')
leader = getLeader(hosts)

if args.leader:
    print("Killing Leader " + leader)
    kill(leader)
else:
    hosts.remove(leader)
    print("Killing follower " + hosts[0])
    kill(hosts[0])
