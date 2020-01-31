import sys
import subprocess
import os 
import shlex

def run(cmd, tag, host):
    logs = "etcd"
    #cmd = "{command} 2>&1 | tee logs/{logs}_{tag}".format(tag=tag,command=cmd, logs=logs)

    cmd = shlex.split(cmd)
    sp = host.popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    FNULL = open(os.devnull, 'w')
    tee = host.popen(['tee', 'logs/{logs}_{tag}_stdout'.format(logs=logs, tag=tag)], stdin = sp.stdout, stdout = FNULL, stderr=FNULL)
    tee = host.popen(['tee', 'logs/{logs}_{tag}_stderr'.format(logs=logs, tag=tag)], stdin = sp.stderr, stdout = FNULL, stderr=FNULL)

    return sp


def start(mn_client, client_id, config):
    client_path = "systems/etcd/clients/"+config['client']+"/client"
    
    args_ips = "".join("http://" + ip + ":2379," for ip in config['cluster_ips'])[:-1]

    cmd =  "{client_path} {ips} {client_id} {client_address}".format(client_path = client_path, ips = args_ips, client_id = str(client_id), client_address = config['client_address'])
    print("Starting client with cmd:" + cmd)

    return run(cmd, "mc" + str(client_id), mn_client) 

