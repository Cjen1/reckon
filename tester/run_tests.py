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
                [
                #    (tag(reads=rr, datasize=ds, servers=ser), hostnames[:ser], default_clients, op_gen.mixed_ops(1000, 1000, ds, rr), failure.NoFailure) for ds in tqdm(variation_datasizes)
                #] + [
                #    (tag(reads=rr, servers=ser, clients=nC), hostnames[:ser], nC, op_gen.mixed_ops(20000, 1000, default_datasize, rr), failure.NoFailure)  for nC in tqdm(variation_clients)
                #] + [
                    (tagFailure("jf" + str(i+1).zfill(3), servers=ser, reads=rr), hostnames[:ser], default_clients, op_gen.mixed_ops(30, 10, default_datasize, rr), lambda ops: failure.SystemFailure(ops, hostnames[:i+1])) for i in tqdm(range(int(math.floor(ser / 2))))
                ] + [
                    (tagFailure("fr" + str(i+1).zfill(3), servers=ser, reads=rr), hostnames[:ser], default_clients, op_gen.mixed_ops(30, 10, default_datasize, rr), lambda ops: failure.SystemFailureRecovery(ops, hostnames[:i+1])) for i in tqdm(range(int(math.floor(ser / 2))))
                ] for ser in variation_servers
            ] for rr in variation_reads
        ]

tests = flatten(testsN)

for test in tests:
    try:
        tester.run_test(test)
    except Exception as e:
        print(e)


