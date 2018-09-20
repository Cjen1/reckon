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
    r = int(reads)
    return str(r).zfill(3) + "R_" + str(servers) + "S_" + str(clients).zfill(3) + "C_" + str(datasize).zfill(7) + "B"

def tagFailure(fail, reads=default_reads, servers=3, clients=default_clients, datasize=default_datasize):
    r = int(reads)
    return fail + "_" + str(r) + "R_" + str(servers) + "S_" + str(clients).zfill(3) + "C_" + str(datasize).zfill(7) + "B"

variation_reads = [0.0, 1.0]   #np.linspace(0, 1, 101, endpoint=True)
variation_clients = np.linspace(1, 300, 100, dtype=int) # Over 1000 clients realistic?.
variation_datasizes = np.logspace(0, np.log2(5)+20,num=20, base=2, endpoint=True, dtype=int) # MAx size chosen as 5MB to not exceed system memory.
variation_servers = [5,3]


# def flatten(a):
#     res = []
#     for i in a:
#         if type(i) == list:
#             res.extend(flatten(i))
#         else:
#             res.append(i)
#     return res
# 
# testsN= [
#             [
#                 [#Standard Test
#                      (
#                         tagFailure("nd", servers=len(cluster), reads=rr), 
#                         cluster,
#                         op_gen.write_ops() if rr == 0  else op_gen.read_ops(),
#                         default_clients, 
#                         30,#seconds
#                         [
#                             failure.no_fail(), 
#                         ] 
#                      ) ] 
#                 for j in range(1) 
#             ] 
#             for cluster in [hostnames[:nser] for nser in [5, 3]]
#         for rr in [0, 100] 
#     ]
# 
# tests = flatten(testsN)
# 
# for args in tests:
#         tester.run_test(*kwargs)

for readratio in [0, 100]:
    for cluster in [hostnames[:nser] for nser in [1,3,5]]:
        tester.run_test(
                tag(servers=len(cluster), reads=readratio),
                cluster,
                op_obj = op_gen.write_ops() if readratio == 0 else op_gen.read_ops(),
                duration=10
                )
