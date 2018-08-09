from utils import op_gen, link, failure, message_pb2 as msg_pb, tester

#---------------------------------------------------------------------------
#------------------------- Hostnames and Tests -----------------------------
#---------------------------------------------------------------------------


hostnames = [
        "caelum-504.cl.cam.ac.uk",
        "caelum-505.cl.cam.ac.uk",
        "caelum-506.cl.cam.ac.uk",
        "caelum-507.cl.cam.ac.uk",
        "caelum-508.cl.cam.ac.uk"
        ]

# test = (tag, hostnames, num_clients, operations, failure_mode)
tests = [
        ("test1", hostnames[:3], 1, op_gen.sequential_keys(100, 100), failure.none()),
        ("test2", hostnames[:3], 4, op_gen.sequential_keys(100, 100), failure.none()),
        ("test3", hostnames[:3], 1, op_gen.sequential_keys(100, 100), failure.crash(10, 0.1, hostnames[:3])),
        ("test4", hostnames[:3], 4, op_gen.sequential_keys(100, 100), failure.crash(10, 0.1, hostnames[:3]))
        ]

for test in tests:
    tester.run_test(test)


