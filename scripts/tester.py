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
        'jitter':0,
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
        'failure_timeout':1,
        'delay_interval':100,
        'notes':{},
        }

def run_test(folder_path, config : Dict[str, Any]):
    run('rm -rf /data/*', shell=True).check_returncode()
    run('mn -c', shell=True).check_returncode()
    run('pkill client', shell=True)

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
        f"--number-nodes {params['nn']} --number-clients {params['nc']} --client {params['client']}",
        f"--link-latency {params['delay']} --link-loss {params['loss']} --link-jitter {params['jitter']}",
        f"--new_client_per_request {params['ncpr']}",
        f"--mtbf {params['mtbf']} --kill-n {params['kill_n']}",
        f"--write-ratio {params['write_ratio']}",
        f"--rate {params['rate']} --duration {params['duration']}",
        f"--arrival-process {params['arrival_process']}",
        f"--system_logs {log_path} --result-location {result_path} --data-dir=/data",
        f"--failure_timeout {params['failure_timeout']}",
        f"--delay_interval {params['delay_interval']}",
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

from numpy.random import default_rng
rng = default_rng()

run_time = datetime.now().strftime("%Y%m%d%H%M%S")
folder_path = f"/results/{run_time}"

actions = []

low_repeat = 3
high_repeat = 50

nn_map = {
        'ocons-conspire-dc': 4,
        'ocons-conspire-mp': 4,
        'ocons-paxos': 3,
        'ocons-raft': 3,
        'etcd': 3
        }
timeout_map = {
        'ocons-conspire-dc': 0.1,
        'ocons-conspire-mp': 0.5,
        'ocons-paxos': 0.5,
        }

## rate-lat systems
#for system, rate, repeat in it.product(
#        [('ocons-conspire-dc', 'ocaml'), ('ocons-conspire-mp', 'ocaml'), ('ocons-paxos', 'ocaml')],
#        [10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000],
#        range(low_repeat)
#        ):
#    system, client = system
#    nn = nn_map[system]
#    timeout = timeout_map[system]
#
#    actions.append(
#            lambda params = {
#                'topo':'wan',
#                'nn':nn,
#                'delay':50,
#                'system':system,
#                'client':client,
#                'rate':rate,
#                'repeat':repeat,
#                'failure_timeout': timeout,
#                'delay_interval': timeout,
#                'duration':10,
#                'tag':'ss-rate-lat',
#                }:
#            run_test(folder_path, params))

## latency results steady state
#for system, repeat in it.product(
#        [('ocons-conspire-dc', 0.04), ('ocons-conspire-dc', 0.05), ('ocons-conspire-dc', 0.06),
#         ('ocons-conspire-mp', 0.5),
#         ('ocons-paxos', 0.5),
#         ],
#        range(low_repeat),
#        ):
#    system, timeout = system
#    nn = nn_map[system]
#
#    actions.append(
#            lambda params = {
#                'topo':'wan',
#                'nn':nn,
#                'delay':50,
#                'system':system,
#                'client':'ocaml',
#                'rate':10000,
#                'repeat':repeat,
#                'failure_timeout': timeout,
#                'delay_interval': timeout,
#                'duration':10,
#                'tag':'ss-latency',
#                }:
#            run_test(folder_path, params))

## leader failure heatmap
#for system, repeat in it.product(
#        ['ocons-conspire-dc', 'ocons-conspire-mp', 'ocons-paxos'],
#        range(low_repeat),
#        ):
#    nn = nn_map[system]
#    timeout = timeout_map[system]
#    actions.append(
#            lambda params = {
#                'topo':'wan',
#                'nn':nn,
#                'delay':50,
#                'system':system,
#                'client':'ocaml',
#                'rate':5000,
#                'repeat':repeat,
#                'failure_timeout': timeout,
#                'delay_interval': timeout,
#                'duration':10,
#                'failure':'leader',
#                'tcpdump':True,
#                'tag':'heatmap',
#                }:
#            run_test(folder_path, params))

# conspire-dc jitter latency
for jitter, timeout, repeat in it.product(
        [0, 0.25, 0.5],
        [0.06, 0.11, 0.16, 0.21, 0.26, 0.31],
        range(low_repeat),
        ):
    nn = 4
    actions.append(
            lambda params = {
                'topo':'wan',
                'nn':nn,
                'delay':50,
                'jitter':jitter,
                'system':'ocons-conspire-dc',
                'client':'ocaml',
                'rate':10000,
                'repeat':repeat,
                'failure_timeout': timeout,
                'delay_interval': timeout,
                'duration':30,
                'failure':'none',
                'tag':'latency-dc-jitter',
                }:
            run_test(folder_path, params))


# jitter failure aggregate
for system, timeout, jitter, repeat in it.product(
        ['ocons-conspire-mp', 'ocons-paxos'],
        [0.06, 0.11, 0.16, 0.21, 0.26, 0.31, 0.36, 0.41],
        [0, 0.25, 0.5],
        range(high_repeat),
        ):
    nn = nn_map[system]
    actions.append(
            lambda params = {
                'topo':'wan',
                'nn':nn,
                'delay':50,
                'jitter':jitter,
                'system':system,
                'client':'ocaml',
                'rate':5000,
                'repeat':repeat,
                'failure_timeout': timeout,
                'delay_interval': timeout,
                'duration':10,
                'failure':'leader',
                'tag':'jitter-aggregate-failure',
                }:
            run_test(folder_path, params))

# Shuffle to isolate ordering effects
rng.shuffle(actions)

print(len(actions))

bar = '##################################################'
for i, act in enumerate(actions):
    print(bar, flush=True)
    print(f"TEST-{i}", flush=True)
    print(bar, flush=True)
    act()

print(bar, flush=True)
print(f"TESTING DONE", flush=True)
print(bar, flush=True)
