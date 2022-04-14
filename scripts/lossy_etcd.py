from subprocess import call, Popen
import shlex
import itertools as it
import numpy as np
from typing import List

#def call_tcp_dump(tag, cmd):
#    tcp_dump_cmd = [
#        "tcpdump",
#        "-i",
#        "any",
#        "-w",
#        ("/results/pcap_" + tag + ".pcap"),
#        "net",
#        "10.0.0.0/16",
#        "-n",
#    ]
#    print(tcp_dump_cmd)
#    p = Popen(tcp_dump_cmd)
#    call(cmd)
#    p.terminate()


def run_test(system='etcd', topo='simple', failure="none", nn='3', nc='1', client='go', rate='1000', duration='60', tag='', kill_n='1', loss='0'):
    config = {
        "system" : system,
        "topo" : topo,
        "nn" : nn,
        "nc" : nc,
        "write_ratio":"1",
        "failure":failure,
        "client":client,
        "rate":rate,
        "duration":duration,
        "tag":tag,
        "kill_n": kill_n,
        "loss":loss,
        }

    tag = (
            "{system}.{topo}.{client}.{failure}.nn_{nn}.nc_{nc}.write_ratio_{write_ratio}.rate_{rate}.duration_{duration}.kill_n_{kill_n}.loss_{loss}.tag_{tag}"
        ).format(**config)

    config['tag'] = tag

    cmd = (
            "python -m reckon {system} {topo} --number-nodes {nn} --number-clients {nc} uniform --write-ratio {write_ratio} " +
            "{failure} --client {client} --system_logs /results/logs " +
            "--rate {rate} --duration {duration} --result-location /results/res_{tag}.res --kill_n {kill_n} --link_loss {loss}"
        ).format(**config)

    print(f"Calling {cmd}\n")

    cmd = shlex.split(cmd)

    call(cmd)

    call(["bash", "scripts/clean.sh"])

from numpy.random import default_rng
rng = default_rng()

for repeat in range(5):
    tag = f"repeat{repeat}"
    nns = [3,5,7,9,11]
    losss : List[float] = [0, 0.01, 0.1, 1, 10]
    minNodes = [False, True]

    params = [v for v in it.product(nns, losss, minNodes)]
    rng.shuffle(params)

    for nn, loss, minNodes in params:
        run_test(failure='kill_n', nn=nn, kill_n=str(int(nn/2)) if minNodes else '0', tag=tag, loss=loss, client='go-tracer', rate=10)
