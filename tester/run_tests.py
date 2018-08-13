from utils import op_gen
from utils import link, failure, message_pb2 as msg_pb, tester

#---------------------------------------------------------------------------
#------------------------- Hostnames and Tests -----------------------------
#---------------------------------------------------------------------------


hostnames = [
        "caelum-506.cl.cam.ac.uk",
        "caelum-507.cl.cam.ac.uk",
        "caelum-508.cl.cam.ac.uk",
	"caelum-505.cl.cam.ac.uk",
	"caelum-504.cl.cam.ac.uk"
        ]

# test = (tag, hostnames, num_clients, operations, failure_mode)
tests = [
	("VeryBasicTest", hostnames[:3], 1, op_gen.sequential_keys(100, 100), failure.none()),
	("OtherBascTest", hostnames[:3], 1, op_gen.mixed_ops(100, 100, 0.5, 1), failure.none()),
	("ThirdBascTest", hostnames[:3], 4, op_gen.mixed_ops(100, 100, 0.5, 4), failure.none()),
        ]

for test in tests:
    tester.run_test(test)


