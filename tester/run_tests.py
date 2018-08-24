from utils import op_gen, link, failure, message_pb2 as msg_pb, tester
import numpy as np

#---------------------------------------------------------------------------
#------------------------- Hostnames and Tests -----------------------------
#---------------------------------------------------------------------------


hostnames = [
        "caelum-506.cl.cam.ac.uk",
        "caelum-507.cl.cam.ac.uk",
        "caelum-508.cl.cam.ac.uk",
	"caelum-504.cl.cam.ac.uk"
	"caelum-505.cl.cam.ac.uk",
        ]

print("starting test")

default_clients  = 1
default_reads    = 0.9
default_datasize = 1024

def tag(reads=default_reads, servers=3, clients=default_clients, datasize=default_datasize):
    r = int(100 * reads)
    return str(r).zfill(2) + "R_" + str(servers) + "S_" + str(clients).zfill(3) + "C_" + str(datasize).zfill(7) + "B"

variation_reads = np.linspace(0, 0.99, 100)
variation_clients = np.linspace(0, 300, 100, dtype=int)
variation_datasizes = np.logspace(0, np.log2(5)+20,num=20, base=2, endpoint=True, dtype=int)

'''
tests = [
    ("Seqw_3s_" + str(nClients) + "c", hostnames[:3], nClients, op_gen.sequential_keys(1000, 100), lambda ops: failure.NoFailure(ops)) for nClients in np.arange(1, 100, 10) 
        ] # Test how systems perform over a range of client numbers

print("completed creation of clients")

tests.extend([
    ("Seqw_3s_1c_" + str(data_size) + "d", hostnames[:3], 1, op_gen.sequential_keys(1000, data_size), lambda ops: failure.NoFailure(ops)) for data_size in np.logspace(0, 20,num=10, base=2, endpoint=True, dtype=int) 
    ]) # Test how systems perform over a range of data sizes
'''
tests = [
            (tag(reads=rr), hostnames[:3], default_clients, op_gen.mixed_ops(10000, 1000, default_datasize, rr)) for rr in variation_reads
        ] + [
            (tag(clients=numClients), hostnames[:3], numClients, op_gen.mixedops(20000, 1000, default_datasize, default_reads))  for numClients in variation_clients
        ] + [
            (tag(datasize=ds), hostnames[:3], default_clients, op_gen.mixed_ops(1000, 1000, ds, default_reads)) for ds in variation_datasizes
        ]


for test in tests:
    tester.run_test(test)


