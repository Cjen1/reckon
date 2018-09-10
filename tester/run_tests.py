from utils import op_gen, link, failure, message_pb2 as msg_pb, tester
import numpy as np
import sys
from tqdm import tqdm
import math

#---------------------------------------------------------------------------
#------------------------- Hostnames and Tests -----------------------------
#---------------------------------------------------------------------------


hostnames = [
        "caelum-506.cl.cam.ac.uk",
        "caelum-507.cl.cam.ac.uk",
        "caelum-508.cl.cam.ac.uk",
	"caelum-504.cl.cam.ac.uk",
	"caelum-505.cl.cam.ac.uk",
        ]

print("starting test")

default_reads    = 0.9
default_clients  = 1
default_datasize = 1024

def tag(reads=default_reads, servers=3, clients=default_clients, datasize=default_datasize):
    r = int(100 * reads)
    return str(r).zfill(3) + "R_" + str(servers) + "S_" + str(clients).zfill(3) + "C_" + str(datasize).zfill(7) + "B"

def tagFailure(fail, reads=default_reads, servers=3, clients=default_clients, datasize=default_datasize):
    r = int(100 * reads)
    return fail + "_" + str(r) + "R_" + str(servers) + "S_" + str(clients).zfill(3) + "C_" + str(datasize).zfill(7) + "B"

variation_reads = [0.0, 1.0]   #np.linspace(0, 1, 101, endpoint=True)
variation_clients = np.linspace(1, 300, 100, dtype=int) # Over 1000 clients realistic?.
variation_datasizes = np.logspace(0, np.log2(5)+20,num=20, base=2, endpoint=True, dtype=int) # MAx size chosen as 5MB to not exceed system memory.
variation_servers = [5,3]


def flatten(a):
    res = []
    for i in a:
        if type(i) == list:
            res.extend(flatten(i))
        else:
            res.append(i)
    return res



testsN=[
            [   
                [#clients dimension
                (
                    tag(clients=nclients),
                    hostnames[:nser],
                    nclients,
                    op_gen.write_ops(1000, default_datasize) if rr == 0 else op_gen.read_ops(100, default_datasize),
                    60,#seconds
                    [failure.no_fail()]
                ) for nclients in variation_clients
                ],
                [#data size dimension
                (
                    tag(datasize=datasize),
                    hostnames[:nser],
                    default_clients,
                    op_gen.write_ops(1000, datasize) if rr == 0 else op_gen.read_ops(100, datasize),
                    60,#seconds
                    [failure.no_fail()]
                ) for datasize in variation_datasizes
                ],
                [#Failure injection
                    (
                        tagFailure("fr" + str(i+1).zfill(3), servers=nser, reads=rr), 
                        hostnames[:nser], 
                        default_clients, 
                        op_gen.write_ops(100, default_datasize) if rr == 0  else op_gen.read_ops(100, default_datasize),
                        30,#seconds
                        [failure.no_fail()] + 
                            [failure.system_crash(host) for host in hostnames[:i+1]] + 
                            [failure.system_recovery(host) for host in hostnames[:i+1]]
                    ) for i in range(int(math.floor(nser / 2)))
                ]
            ] for nser in [3, 5]
        for rr in [0, 100]
        ]

tests = flatten(testsN)

for test in tests:
        tester.run_test(test)


