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

tests = [
    ("Seqw_3s_" + nClients + "c", hostnames[:3], nClients, op_gen.sequential_keys(10000, 100), lambda ops: failure.NoFailure(ops)) for nClients in np.arrange(1, 100, 10) 
        ] # Test how systems perform over a range of client numbers

tests.extend([
    ("Seqw_3s_1c_" + data_size + "d", hostnames[:3], 1, op_gen.sequential_keys(1000, data_size), lambda ops: failure.NoFailure(ops)) for data_size in np.linspace(0, 1048576, dtype = int, endpoint=True)  
    ] # Test how systems perform over a range of data sizes

for test in tests:
    tester.run_test(test)


