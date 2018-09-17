from subprocess import call, check_output
from sys import argv
import argparse
import socket
import requests
import etcd

def kill(host):
    call (["ssh", host, "docker stop zookeeper"])

def leader(host):
    output = check_output(['echo stat | nc '+socket.gethostbyname(host)+' 2181 | grep Mode'], shell=True)
    if 'leader' in output:
        return True
    return False


def killLeader(cluster):
    leaderNode = None
    for host in cluster:
        output = check_output(['echo stat | nc '+socket.gethostbyname(host)+' 2181 | grep Mode'], shell=True)
        if leader(host):
            leaderNode = host
            break
    if leaderNode == None:
        print("Error: No leader to kill")
        return

    print("Killing leader: " +leaderNode)
    kill(leaderNode)

parser = argparse.ArgumentParser(description='Stops the either a given server or the leader of a cluster')
parser.add_argument('--cluster', '-c')
parser.add_argument('--leader', '-l', action='store_true')
args = parser.parse_args()

hosts = args.cluster.split(',')
if args.leader:
    killLeader(hosts)
else:
    if not(leader(hosts[0])):
        kill(hosts[0])
    else:
        kill(hosts[1])
