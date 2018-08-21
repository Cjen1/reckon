from utils import op_gen, link, failure, message_pb2 as msg_pb, tester

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
        #("Seqw_3s_1c",   hostnames[:3],  1,  op_gen.sequential_keys(1000, 100), lambda ops: failure.NoFailure(ops)),
        #("Seqw_3s_4c",   hostnames[:3],  4,  op_gen.sequential_keys(1000, 100), lambda ops: failure.NoFailure(ops)),
        #("Seqw_3s_8c",   hostnames[:3],  8,  op_gen.sequential_keys(1000, 100), lambda ops: failure.NoFailure(ops)),
        #("Seqw_3s_12c",  hostnames[:3],  12, op_gen.sequential_keys(1000, 100), lambda ops: failure.NoFailure(ops)),
        #("Seqw_3s_16c",  hostnames[:3],  16, op_gen.sequential_keys(1000, 100), lambda ops: failure.NoFailure(ops)),
        ("Seqw_f_3s_1c",    hostnames[:3],  1,  op_gen.sequential_keys(10, 100), lambda ops: failure.SystemFailure(ops, hostnames[0:1])),
        ("Seqw_fr_3s_1c",   hostnames[:3],  1,  op_gen.sequential_keys(10, 100), lambda ops: failure.SystemFailureRecovery(ops, hostnames[0:1]))
        ]

for test in tests:
    tester.run_test(test)


