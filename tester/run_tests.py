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
#        ("SplitTest-5xSlowRestart-00r-1c-10f-3s", hostnames[:3], 1, op_gen.sequential_keys(1000, 100), failure.crash(10, 0.5, hostnames[:3])),# Previously "Test 3"
#        ("SplitTest-5xSlowRestart-00r-4c-10f-3s", hostnames[:3], 4, op_gen.sequential_keys(1000, 100), failure.crash(10, 0.5, hostnames[:3])),# Previously "Test 4"
#	("SplitTest-5xSlowRestart-30r-1c-10f-3s", hostnames[:3], 1, op_gen.mixed_ops(1000, 100, 0.3, 1), failure.crash(10, 0.5, hostnames[:3])),
#	("SplitTest-5xSlowRestart-30r-4c-10f-3s", hostnames[:3], 4, op_gen.mixed_ops(1000, 100, 0.3, 4), failure.crash(10, 0.5, hostnames[:3])),
#	("SplitTest-5xSlowRestart-60r-1c-10f-3s", hostnames[:3], 1, op_gen.mixed_ops(1000, 100, 0.6, 1), failure.crash(10, 0.5, hostnames[:3])),
#	("SplitTest-5xSlowRestart-60r-4c-10f-3s", hostnames[:3], 4, op_gen.mixed_ops(1000, 100, 0.6, 4), failure.crash(10, 0.5, hostnames[:3])),
#	("SplitTest-5xSlowRestart-90r-1c-10f-3s", hostnames[:3], 1, op_gen.mixed_ops(1000, 100, 0.9, 1), failure.crash(10, 0.5, hostnames[:3])),
#	("SplitTest-5xSlowRestart-90r-4c-10f-3s", hostnames[:3], 4, op_gen.mixed_ops(1000, 100, 0.9, 4), failure.crash(10, 0.5, hostnames[:3])),
#        ("SplitTest-5xSlowRestart-00r-1c-10f-5s", hostnames[:5], 1, op_gen.sequential_keys(1000, 100), failure.crash(10, 0.5, hostnames[:3])),# Previously "Test 3"
#        ("SplitTest-5xSlowRestart-00r-4c-10f-5s", hostnames[:5], 4, op_gen.sequential_keys(1000, 100), failure.crash(10, 0.5, hostnames[:3])),# Previously "Test 4"
#	("SplitTest-5xSlowRestart-30r-1c-10f-5s", hostnames[:5], 1, op_gen.mixed_ops(1000, 100, 0.3, 1), failure.crash(10, 0.5, hostnames[:5])),
#	("SplitTest-5xSlowRestart-30r-4c-10f-5s", hostnames[:5], 4, op_gen.mixed_ops(1000, 100, 0.3, 4), failure.crash(10, 0.5, hostnames[:5])),
#	("SplitTest-5xSlowRestart-60r-1c-10f-5s", hostnames[:5], 1, op_gen.mixed_ops(1000, 100, 0.6, 1), failure.crash(10, 0.5, hostnames[:5])),
#	("SplitTest-5xSlowRestart-60r-4c-10f-5s", hostnames[:5], 4, op_gen.mixed_ops(1000, 100, 0.6, 4), failure.crash(10, 0.5, hostnames[:5])),
#	("SplitTest-5xSlowRestart-90r-1c-10f-5s", hostnames[:5], 1, op_gen.mixed_ops(1000, 100, 0.9, 1), failure.crash(10, 0.5, hostnames[:5])),
#	("SplitTest-5xSlowRestart-90r-4c-10f-5s", hostnames[:5], 4, op_gen.mixed_ops(1000, 100, 0.9, 4), failure.crash(10, 0.5, hostnames[:5])),
        ("SplitTest-9xSlowRestart-00r-1c-10f-3s", hostnames[:3], 1, op_gen.sequential_keys(1000, 100), failure.crash(10, 0.9, hostnames[:3])),# Previously "Test 3"
        ("SplitTest-9xSlowRestart-00r-4c-10f-3s", hostnames[:3], 4, op_gen.sequential_keys(1000, 100), failure.crash(10, 0.9, hostnames[:3])),# Previously "Test 4"
	("SplitTest-9xSlowRestart-30r-1c-10f-3s", hostnames[:3], 1, op_gen.mixed_ops(1000, 100, 0.3, 1), failure.crash(10, 0.9, hostnames[:3])),
	("SplitTest-9xSlowRestart-30r-4c-10f-3s", hostnames[:3], 4, op_gen.mixed_ops(1000, 100, 0.3, 4), failure.crash(10, 0.9, hostnames[:3])),
	("SplitTest-9xSlowRestart-60r-1c-10f-3s", hostnames[:3], 1, op_gen.mixed_ops(1000, 100, 0.6, 1), failure.crash(10, 0.9, hostnames[:3])),
	("SplitTest-9xSlowRestart-60r-4c-10f-3s", hostnames[:3], 4, op_gen.mixed_ops(1000, 100, 0.6, 4), failure.crash(10, 0.9, hostnames[:3])),
	("SplitTest-9xSlowRestart-90r-1c-10f-3s", hostnames[:3], 1, op_gen.mixed_ops(1000, 100, 0.9, 1), failure.crash(10, 0.9, hostnames[:3])),
	("SplitTest-9xSlowRestart-90r-4c-10f-3s", hostnames[:3], 4, op_gen.mixed_ops(1000, 100, 0.9, 4), failure.crash(10, 0.9, hostnames[:3])),
        ("SplitTest-9xSlowRestart-00r-1c-10f-5s", hostnames[:5], 1, op_gen.sequential_keys(1000, 100), failure.crash(10, 0.9, hostnames[:3])),# Previously "Test 3"
        ("SplitTest-9xSlowRestart-00r-4c-10f-5s", hostnames[:5], 4, op_gen.sequential_keys(1000, 100), failure.crash(10, 0.9, hostnames[:3])),# Previously "Test 4"
	("SplitTest-9xSlowRestart-30r-1c-10f-5s", hostnames[:5], 1, op_gen.mixed_ops(1000, 100, 0.3, 1), failure.crash(10, 0.9, hostnames[:5])),
	("SplitTest-9xSlowRestart-30r-4c-10f-5s", hostnames[:5], 4, op_gen.mixed_ops(1000, 100, 0.3, 4), failure.crash(10, 0.9, hostnames[:5])),
	("SplitTest-9xSlowRestart-60r-1c-10f-5s", hostnames[:5], 1, op_gen.mixed_ops(1000, 100, 0.6, 1), failure.crash(10, 0.9, hostnames[:5])),
	("SplitTest-9xSlowRestart-60r-4c-10f-5s", hostnames[:5], 4, op_gen.mixed_ops(1000, 100, 0.6, 4), failure.crash(10, 0.9, hostnames[:5])),
	("SplitTest-9xSlowRestart-90r-1c-10f-5s", hostnames[:5], 1, op_gen.mixed_ops(1000, 100, 0.9, 1), failure.crash(10, 0.9, hostnames[:5])),
	("SplitTest-9xSlowRestart-90r-4c-10f-5s", hostnames[:5], 4, op_gen.mixed_ops(1000, 100, 0.9, 4), failure.crash(10, 0.9, hostnames[:5])),
        ]

for test in tests:
    tester.run_test(test)


