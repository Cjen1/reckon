from subprocess import call
from sys import argv
import argparse
import socket
import requests


def kill(host):
    call (["ssh", host, "docker stop consul"])

def getLeader(cluster):
    host_lookup = {socket.gethostbyname(host) : host for host in cluster}

    resp = requests.get('http://127.0.0.1:8500/v1/status/leader')
    # Remove surrounding quotes then select first part of "127.0.0.1:8500"
    leader_ip = resp.text[1:-1].split(':')[0]
    leader = host_lookup[leader_ip]
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
if args.leader:
    killLeader(hosts)
else:
    if(getLeader(hosts) == hosts[0]):
        kill(hosts[1])
    else:
        kill(hosts[1])
