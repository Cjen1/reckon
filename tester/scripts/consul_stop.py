from subprocess import call
from sys import argv
import argparse
import socket
import requests


def kill(host):
    call (["ssh", host, "docker stop consul"])

def killLeader(cluster):
    host_lookup = {socket.gethostbyname(host) : host for host in cluster}

    resp = requests.get('http://127.0.0.1:8500/v1/status/leader')
    leader_ip = resp.split(':')[0]

    leader = host_lookup[leader_ip]

    print("Killing leader: " +leader)

    kill(leader)
    



parser = argparse.ArgumentParser(description='Stops the either a given server or the leader of a cluster')
parser.add_argument('--hosts', '-h')
parser.add_argument('--leader', '-l', action='store_true')
args = parser.parse_args()

hosts = args.hosts.split(',')
if args.leader:
    killLeader(hosts)
else:
    kill(hosts[0])
