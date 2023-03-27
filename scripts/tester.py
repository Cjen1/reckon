from subprocess import call, Popen, run
import shlex
import itertools as it
import uuid
from datetime import datetime
import json
import os

from typing import Dict, Any, AnyStr

import math

def call_tcp_dump(tcpdump_path, cmd):
    tcp_dump_cmd = [
        "tcpdump",
        "-i",
        "any",
        "-w",
        tcpdump_path,
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
        'delay':20,
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

def run_test(folder_path, config : Dict[str, Any]):
    run('rm -rf /data/*', shell=True).check_returncode()
    run('mn -c', shell=True).check_returncode()

    uid = uuid.uuid4()

    # Set params
    params = default_parameters.copy()
    for k,v in config.items():
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

    run(f'mkdir -p {result_folder}', shell=True).check_returncode()
    run(f'mkdir -p {log_path}', shell=True).check_returncode()

    with open(config_path, "w") as of:
        json.dump(params, of)

    print(f"RUNNING TEST")
    print(cmd)

    cmd = shlex.split(cmd)

    if params['tcpdump']:
        call_tcp_dump(tcpdump_path, cmd)
    else:
        call(cmd)

#from numpy.random import default_rng
#rng = default_rng()

run_time = datetime.now().strftime("%Y%m%d%H%M%S")
folder_path = f"/results/{run_time}"

actions = []

## Leader election heat maps
#for sys, repeat in it.product(
#        [('etcd', 'go'), ('zookeeper', 'java'),
#        ('etcd-pre-vote', 'go'), ('zookeeper-fle', 'java')],
#        range(10),
#        ):
#    system, client = sys
#    actions.append(
#            lambda params = {
#                'failure': 'leader-only',
#                'system':system,
#                'client':client,
#                'duration':30,
#                'repeat':repeat,
#                'rate':5000,
#                'delay':50,
#                'nn':str(3),
#                'tcpdump': True,
#                }:
#            run_test(folder_path, params)
#            )

# Leader election bulk
for sys, repeat in it.product(
        [('etcd', 'go'), ('zookeeper', 'java'),
        ('etcd-pre-vote', 'go'), ('zookeeper-fle', 'java')],
        range(100),
        ):
    system, client = sys
    actions.append(
            lambda params = {
                'failure': 'leader-only',
                'system':system,
                'client':client,
                'duration':30,
                'repeat':repeat,
                'rate':5000,
                'delay':50,
                'nn':3,
                }:
            run_test(folder_path, params)
            )

# Steady latency (DC and WAN)
for sys, repeat in it.product(
        [('etcd', 'go'), ('zookeeper', 'java')],
        range(10)
        ):
    system, client = sys
    actions.append(
            lambda params = {
                'failure': 'none',
                'system':system,
                'client':client,
                'duration':30,
                'rate':5000,
                'delay':50,
                'nn':3,
                'repeat':repeat,
                }:
            run_test(folder_path, params)
            )
    actions.append(
            lambda params = {
                'failure': 'none',
                'system':system,
                'client':client,
                'duration':30,
                'rate':5000,
                'delay':0,
                'nn':3,
                'repeat':repeat,
                }:
            run_test(folder_path, params)
            )

# Steady latency WAN
for sys, rate, repeat in it.product(
        [('etcd', 'go'), ('zookeeper', 'java')],
        [1000,5000,10000,15000,20000,25000,30000,35000],
        range(10),
        ):
    system, client = sys
    actions.append(
            lambda params = {
                'failure': 'none',
                'system':system,
                'client':client,
                'duration':30,
                'rate':rate,
                'delay':50,
                'nn':3,
                'repeat':repeat,
                'notes':'rate-lat',
                }:
            run_test(folder_path, params)
            )
# Shuffle to isolate ordering effects
#rng.shuffle(actions)

print(len(actions))

bar = '##################################################'
#for i, act in enumerate(actions):
#    print(bar, flush=True)
#    print(f"TEST-{i}", flush=True)
#    print(bar, flush=True)
#    act()

print(bar, flush=True)
print(f"TESTING DONE", flush=True)
print(bar, flush=True)
