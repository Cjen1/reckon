from subprocess import call, check_output
from sys import argv
import argparse
import socket
import requests
import etcd

def kill(host):
    call (["ssh", host, "docker stop zookeeper"])

def getLeader(cluster):
    LeaderNode = None
    for host in cluster:
        output = check_output(['echo stat | nc ' + socket.gethostbyname(host) + ' 2181 | grep Mode'], shell=True)
        if 'leader' in output:
            LeaderNode = host
            break;
    if LeaderNode == None:
        print("Error: No Leader to kill")
        return ""

    return LeaderNode

parser = argparse.ArgumentParser(description='Stops the either a given server or the leader of a cluster')
parser.add_argument('--cluster', '-c')
parser.add_argument('--leader', '-l', action='store_true')
args = parser.parse_args()

hosts = args.cluster.split(',')
leader = getLeader(hosts)
if args.leader:
    print("Killing leader: " + leader)
    kill(leader)
else:
    hosts.remove(leader)
    candidate = hosts[0]
    print("Killing follower: " + candidate)
    kill(candidate)
