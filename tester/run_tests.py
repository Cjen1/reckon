from utils import tester, failure, op_gen 
import socket
import numpy as np

hostnames = [
        "caelum-504.cl.cam.ac.uk",
        "caelum-505.cl.cam.ac.uk",
        "caelum-506.cl.cam.ac.uk",
        "caelum-507.cl.cam.ac.uk",
        "caelum-508.cl.cam.ac.uk"
        ]

endpoints = [ "http://"+socket.gethostbyname(host)+":2379" for host in hostnames]

# TODO make these values make sense ie pull from industrial
MTBF = np.linspace(0.1, 10, 5)
MTTR = np.linspace(0.1, 1, 5)
Client_Nums = [int(i) for i in np.logspace(0, 3, 10)]
Endpoint_Nums = [1,3]
Key_Sizes = [4 ** i for i in range(12)[1:]]
Sample_Size = 1000

# tests = [(tag, test, hostnames, failure_injection), ...]
def test_gen_no_failure(client_num = 1, endpoint_num = 3, key_size = 4, sample_size = 1000):
    return (
        "Sequential-{client_num}C-{endpoint_num}S-{key_size}K".format(
            client_num=client_num,
            endpoint_num=endpoint_num,
            key_size=key_size),
        lambda client: tester.multi_client(client, endpoints[:endpoint_num], client_num, op_gen.sequential_keys(sample_size, key_size)),
        hostnames[:endpoint_num], failure.none())

# tests = [(tag, test, hostnames, failure_injection), ...]
def test_gen_crash(client_num = 1, endpoint_num = 3, key_size = 4, sample_size = 1000, mtbf = 0.5, mttr = 0.5):
    return (
        "Sequential-{client_num}C-{endpoint_num}S-{key_size}K".format(
            client_num=client_num,
            endpoint_num=endpoint_num,
            key_size=key_size),
        lambda client: tester.multi_client(client, endpoints[:endpoint_num], client_num, op_gen.sequential_keys(Sample_Size, key_size)),
        hostnames[:endpoint_num], failure.crash(mtbf, mttr, hostnames[:endpoint_num] ))


tests = []


for client_num in Client_Nums:
    tests.append(test_gen_no_failure(client_num = client_num))

for mtbf in MTBF:
    for mttr in MTTR:
        tests.append(test_gen_crash(mtbf = mtbf, mttr = mttr))

for endpoint_num in Endpoint_Nums:
    tests.append(test_gen_no_failure(endpoint_num  = endpoint_num))

for key_size in Key_Sizes:
    tests.append(test_gen_no_failure(key_size = key_size))

tester.run_tests(tests)

