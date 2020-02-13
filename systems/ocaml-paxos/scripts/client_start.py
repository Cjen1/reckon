import subprocess
import os
import shlex

def clean_address(address):
    try:
        os.unlink(address)
    except OSError:
        if os.path.exists(address):
            raise

def new_pipe(address):
    print("Cleaning address")
    clean_address(address)
    print("creating fifo")
    os.mkfifo(address)
    print("created fifo")
    f= os.open(address, os.O_RDONLY | os.O_NONBLOCK)
    print("opened file")
    return f

def start(mn_client, client_id, config):
    ips = config['cluster_ips']
    client_path = "systems/ocaml-paxos/clients/"+config['client']+"/client"
    
    tags = ["op_h" + str(i+1) for i,ip in enumerate(ips)]

    client_port=5001
    endpoints = "".join(
            "{tag}={ip}:{client_port},".format(tag=tag,ip=ip,client_port=client_port)
            for tag,ip in zip(tags, ips)
            )[:-1]

    print("Starting client: " + str(client_id))
    return mn_client.popen(
            [client_path, endpoints, config['client_address'], str(client_id)],
            stdout = sys.stdout, stderr = sys.stderr, close_fds = True
            )
