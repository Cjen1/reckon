import subprocess
import os
import shlex
import time

def get_tag(host):
    return "mc_" + host.name

def run(cmd, host):
    #cmd = "perf record --call-graph dwarf -g -o /results/perf.data -- " + cmd
    cmd = shlex.split(cmd)
    sp = host.popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    FNULL = open(os.devnull, 'w')

    ctime = time.localtime()
    time_tag = time.strftime("%H:%M:%S", ctime)

    subprocess.Popen(['tee', 'logs/' + time_tag + '_out_' + get_tag(host)], stdin=sp.stdout, stdout=FNULL, stderr=FNULL)
    subprocess.Popen(['tee', 'logs/' + time_tag + '_err_' + get_tag(host)], stdin=sp.stderr, stdout=FNULL, stderr=FNULL)

    return sp

def clean_address(address):
    if os.path.exists(address):
        os.unlink(address)

def setup_pipes_and_start_client(address, cmd, host):
    tag = get_tag(host)

    print(tag + "Creating a new pipe: " + address)
    print(tag + "Cleaning address")
    clean_address(address)
    print(tag + "creating fifo")
    os.mkfifo(address)
    print(tag + "Created fifo, starting client with: " + cmd)
    sp = run(cmd, host)
    print(tag + "Created client, opening pipe for reading")
    f=open(address, "r")
    print(tag + "opened pipe")
    return sp.stdin, f

def start(mn_client, client_id, config):
    print("starting microclient: " + str(client_id))
    client_path = "systems/etcd/clients/"+config['client']+"/client"
    
    args_ips = ",".join("http://" + host.IP() + ":2379" for host in config['cluster'])

    result_address = "src/utils/sockets/" + get_tag(mn_client)

    cmd = "{client_path} {ips} {client_id} {result_pipe}".format(
            client_path = client_path,
            ips = args_ips,
            client_id = str(client_id),
            result_pipe = result_address
            )


    return setup_pipes_and_start_client(result_address, cmd, mn_client)

