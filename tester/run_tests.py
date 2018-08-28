from utils import op_gen, link, failure, message_pb2 as msg_pb, tester
import numpy as np
import sys

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

default_reads    = 0.9
default_clients  = 1
default_datasize = 1024

def tag(reads=default_reads, servers=3, clients=default_clients, datasize=default_datasize):
    r = int(100 * reads)
    return str(r).zfill(2) + "R_" + str(servers) + "S_" + str(clients).zfill(3) + "C_" + str(datasize).zfill(7) + "B"

variation_reads = np.linspace(0, 1, 101, endpoint=True)
variation_clients = np.linspace(1, 300, 100, dtype=int)  # Experimentally determined maximum number of clients to be ~300 before crash.
variation_datasizes = np.logspace(0, np.log2(5)+20,num=20, base=2, endpoint=True, dtype=int) # MAx size chosen as 5MB to not exceed system memory.

tests = [
            (tag(reads=rr), hostnames[:3], default_clients, op_gen.mixed_ops(10000, 1000, default_datasize, rr)) for rr in variation_reads
        ] + [
            (tag(clients=nC), hostnames[:3], nC, op_gen.mixed_ops(20000, 1000, default_datasize, default_reads))  for nC in variation_clients
        ] + [
            (tag(datasize=ds), hostnames[:3], default_clients, op_gen.mixed_ops(1000, 1000, ds, default_reads)) for ds in variation_datasizes
        ]


for test in tests:
    try:
        tester.run_test(test)
    except:
        print("Unexpected error:" + sys.exc_info()[0])


