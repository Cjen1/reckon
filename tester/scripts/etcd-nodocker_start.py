from subprocess import call, check_output
from sys import argv
import argparse
import socket
import requests
import etcd
import socket

def recover(host, hosts):
    nodename = {host: "etcd-node-" + str(i+1) for i, host in enumerate(hosts)}

    # Checks for running screens
    output = check_output(['ssh', host, 'screen -list'])
    # If etcd_background screen not running start it
    if not 'etcd_background' in output:
        setup_remote(host, socket.gethostbyname(host), nodename[host], hosts)

def setup_remote(host, ip, node_name, hosts):
    cluster = "".join("etcd-node-" + str(i+1) + "=http://" + host + ":2380," for i, host in enumerate(hosts))[:-1]
    call([
        "ssh",
        host,
        (   "screen -d -S etcd_background -m " +
            "./go/bin/etcd " +
            "--name {name} " + 
            "--initial-advertise-peer-urls http://127.0.1.1:2380 --listen-peer-urls http://0.0.0.0:2380 " + 
            "--advertise-client-urls http://{ip}:2379 --listen-client-urls http://0.0.0.0:2379 " + 
            "--initial-cluster {cluster} " +
            "--initial-cluster-state {cluster_state} --initial-cluster-token {cluster_token}"
        ).format(
            registry="gcr.io/etcd-development/etcd", 
            etcd_ver="v3.3.8", 
            name=node_name, 
            ip=ip, 
            cluster=cluster, 
            cluster_state="new", 
            cluster_token="urop_cluster")
        ])

parser = argparse.ArgumentParser(description='Starts each server in the cluster')
parser.add_argument('--cluster', '-c')
args = parser.parse_args()

hosts = args.cluster.split(',')

for host in hosts:
    recover(host)
