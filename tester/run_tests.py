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
        ("SplitTest-9xSlowRestart-00r-1c-10f-3s", hostnames[:3], 1, op_gen.sequential_keys(1000, 100), failure.crash(10, 0.9, hostnames[:3])),# Previously "Test 3"
        ("SplitTest-9xSlowRestart-00r-4c-10f-3s", hostnames[:3], 4, op_gen.sequential_keys(1000, 100), failure.crash(10, 0.9, hostnames[:3])),# Previously "Test 4"
        ("SplitTest-9xSlowRestart-00r-1c", hostnames[:3], 1, op_gen.sequential_keys(1000, 100), failure.none),# Previously "Test 3"
        ("SplitTest-9xSlowRestart-00r-4c", hostnames[:3], 4, op_gen.sequential_keys(1000, 100), failure.none),# Previously "Test 4"
        ]

for test in tests:
    tester.run_test(test)


