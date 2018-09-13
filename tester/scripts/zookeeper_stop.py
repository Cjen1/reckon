from subprocess import call, check_output
from sys import argv
import argparse
import socket
import requests
import etcd

def kill(host):
    call (["ssh", host, "docker stop zookeeper"])

def killLeader(cluster):
    leader = None
    for host in cluster:
        output = check_output(['echo stat | nc '+socket.gethostbyname(host)+' 2181 | grep Mode'], shell=True)
        if 'leader' in output:
            leader = host
            break
    if leader == None:
        print("Error: No leader to kill")
        return

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
