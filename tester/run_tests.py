from utils import op_gen, link, failure, message_pb2 as msg_pb, tester
import numpy as np
import sys
from tqdm import tqdm
import math
from subprocess import call
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
    r = int(reads*100)
    return str(r).zfill(3) + "R_" + str(servers) + "S_" + str(clients).zfill(3) + "C_" + str(datasize).zfill(7) + "B"

def tagFailure(fail, reads=default_reads, servers=3, clients=default_clients, datasize=default_datasize):
    r = int(reads*100)
    return fail + "_" + str(r) + "R_" + str(servers) + "S_" + str(clients).zfill(3) + "C_" + str(datasize).zfill(7) + "B"

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

for cluster in [hostnames[:nser] for nser in [3,5]]:
    # Reads and write tests
    for readratio in [0, 1]:
   #     # Pure throughput
   #     tester.run_test(
   #             tag(servers=len(cluster), reads=readratio),
   #             cluster,
   #             op_obj=op_gen.write_ops() if readratio == 0 else op_gen.read_ops(),
   #             duration=30
   #             )
   #     # Pure throughput
         for ncli in [1, 20]:
             tester.run_test(
                     tag(servers=len(cluster), clients=ncli, reads=readratio) + '_thru',
                     cluster,
                     num_clients=ncli,
                     op_obj=op_gen.write_ops(data_size=1024*1024*5) if readratio == 0 else op_gen.read_ops(data_size=5*1024**2),
                     duration=30
                     )
   # 
   #     if(len(cluster) > 1):          #For 1 server, killing the server will result in crash
   #         # Leader Failure
   #         tester.run_test(
   #                 tagFailure("lf", servers=len(cluster), reads=readratio),
   #                 cluster,
   #                 op_obj=op_gen.write_ops() if readratio == 0 else op_gen.read_ops(),
   #                 duration=10,
   #                 failures=[
   #                     failure.no_fail(),
   #                     failure.system_leader_crash(cluster),
   #                     failure.system_full_recovery(cluster)
   #                     ]
   #                 )

   #          # Follower Failure
   #         tester.run_test(
   #                 tagFailure("ff", servers=len(cluster), reads=readratio),
   #                 cluster,
   #                 op_obj=op_gen.write_ops() if readratio == 0 else op_gen.read_ops(),
   #                 duration=10,
   #                 failures=[
   #                     failure.no_fail(),
   #                     failure.system_follower_crash(cluster),
   #                     failure.system_full_recovery(cluster)
   #                     ]
   #                 )

   #     # Client number tests
   #     for nclients in np.linspace(1, 300, 100, dtype=int): 
   #         tester.run_test(
   #                 tag(servers=len(cluster), clients=nclients, reads=readratio),
   #                 cluster,
   #                 op_obj=op_gen.write_ops() if readratio == 0 else op_gen.read_ops(),
   #                 num_clients=nclients,
   #                 duration=30,
   #                 failures=[
   #                     failure.no_fail()
   #                     ]
   #                 )

   #     # Data size tests
   #     for data_size in np.logspace(0, np.log2(5)+20,num=20, base=2, endpoint=True, dtype=int): # Max size chosen as 5MB to not exceed system memory.
   #         tester.run_test(
   #                 tag(datasize=data_size, servers=len(cluster), clients=nclients, reads=readratio),
   #                 cluster,
   #                 op_obj=op_gen.write_ops(data_size=data_size) if readratio == 0 else op_gen.read_ops(data_size=data_size),
   #                 duration=30,
   #                 failures=[
   #                     failure.no_fail()
   #                     ]
   #                 )


   #         
   # # Read vs writes tests
   # for readratio in [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]:
   #     tester.run_test(
   #             tag(servers=len(cluster), reads=readratio),
   #             cluster,
   #             op_obj=op_gen.mixed_ops(ratio=readratio),
   #             duration=30
   #             )

    call(['zip', 'results' + str(len(cluster)) + 'S.zip', 'results/*'])
    call(['rm', 'results/*'])



