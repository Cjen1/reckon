from subprocess import call, Popen
import shlex
import itertools as it
import uuid
from datetime import datetime
import json
import os

import math

def call_tcp_dump(tag, cmd):
    tcp_dump_cmd = [
        "tcpdump",
        "-i",
        "any",
        "-w",
        ("/results/pcap_" + tag + ".pcap"),
        "net",
        "10.0.0.0/16",
        "-n",
    ]
    print(tcp_dump_cmd)
    p = Popen(tcp_dump_cmd)
    call(cmd)
    p.terminate()

default_parameters = {
        'system':'etcd',
        'client':'go',
        'topo':'simple',
        'failure':'none',
        'nn':3,
        'nc':1,
        'delay':0,
        'loss':0,
        'ncpr':'False',
        'mtbf':1,
        'kill_n':0,
        'write_ratio':1,
        'rate':1000,
        'duration':60,
        'tag':'tag',
        'tcpdump':False,
        'arrival_process':'uniform',
        'repeat':-1,
        'notes':{},
        }

def run_test(folder_path, config):
    uid = uuid.uuid4()

    # Set params
    params = default_parameters.copy()
    for k,v in config:
        params[k] = v
    del config

    assert (params['repeat'] != -1)

    result_folder = f"{folder_path}/{uid}/"
    log_path    = result_folder + f"logs"
    config_path = result_folder + f"config.json"
    result_path = result_folder + f"res.json"
    tcpdump_path= result_folder + f"tcpdump.pcap"

    cmd = " ".join([
        f"python -m reckon {params['system']} {params['topo']} {params['failure']}",
        f"--number-nodes {params['nn']} --number-clients {params['nc']} --client {params['client']} --link-latency {params['delay']} --link-loss {params['loss']}",
        f"--new_client_per_request {params['ncpr']}",
        f"--mtbf {params['mtbf']} --kill-n {params['kill_n']}",
        f"--write-ratio {params['write_ratio']}",
        f"--rate {params['rate']} --duration {params['duration']}",
        f"--arrival-process {params['arrival_process']}",
        f"--system_logs {log_path} --result-location {result_path} --data-dir=/data",
        ])

    os.mkdir(result_folder)
    os.mkdir(log_path)

    with open(config_path, "w") as of:
        json.dump(params, of)

    print(f"RUNNING TEST")
    print(cmd)

    cmd = shlex.split(cmd)

    if params['tcpdump']:
        call_tcp_dump(tcpdump_path, cmd)
    else:
        call(cmd)

from numpy.random import default_rng
rng = default_rng()

run_time = datetime.now().strftime("%Y%m%d%H%M%S")
folder_path = f"/results/{run_time}"

actions = []

# Steady state graphs
for sys, nn, rate, repeat in it.product(
        [('etcd', 'go'), ('zookeeper', 'java')],
        [1,3,5,7],
        [1000, 5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000, 45000, 50000],
        range(10),
        ):
    system, client = sys
    actions.append(
            lambda params = {
                'system':system,
                'client':client,
                'duration':30,
                'repeat':repeat,
                'rate':rate,
                'nn':str(nn),
                }:
            run_test(folder_path, params)
            )

# Leader faults
for sys, repeat in it.product(
        [('etcd', 'go'), ('zookeeper', 'java')],
        range(100)
        ):
    system, client = sys
    actions.append(
            lambda params={
                'failure':'leader',
                'system':system,
                'client':client,
                'duration':30,
                'repeat':repeat,
                }:
            run_test(folder_path, params)
            )

# Shuffle to isolate ordering effects
rng.shuffle(actions)

for act in actions:
    act()
