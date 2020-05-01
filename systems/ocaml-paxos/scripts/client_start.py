import subprocess
import os
import shlex

def tag(host):
    return host.name

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
    #f= os.open(address, os.O_RDONLY | os.O_NONBLOCK)
    f=open(address, 'r')
    print("opened file")
    return f

def run(cmd, tag, host):
    cmd = shlex.split(cmd)
    sp = host.popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    FNULL = open(os.devnull, 'w')

    subprocess.Popen(['tee', 'logs/out_' + tag], stdin=sp.stdout, stdout=FNULL, stderr=FNULL)
    subprocess.Popen(['tee', 'logs/err_' + tag], stdin=sp.stderr, stdout=FNULL, stderr=FNULL)

    return sp

def start(mn_client, client_id, config):
    print("starting microclient: " + str(client_id))
    client_path = "systems/ocaml-paxos/clients/"+config['client']+"/client"
    
    args_caps = ",".join("/data/cli_" + tag(host) for host in config['cluster'])

    result_address = "src/utils/sockets/" + str(client_id)

    cmd =  "{client_path} {caps} {client_id} {result_pipe}".format(
            client_path = client_path,
            caps = args_caps,
            client_id = str(client_id),
            result_pipe = result_address
            )
    print("Starting client with cmd:" + cmd)

    sp = run(cmd, "mc" + str(client_id), mn_client)

    results = new_pipe(result_address)
    print(str(client_id) + ": created new pipe successfully")


    return sp.stdin, results

