from utils import tester, failure, op_gen 
import socket

hostnames = [
        "caelum-504.cl.cam.ac.uk",
        "caelum-505.cl.cam.ac.uk",
        "caelum-506.cl.cam.ac.uk",
        "caelum-507.cl.cam.ac.uk",
        "caelum-508.cl.cam.ac.uk"
        ]

endpoints = [ "http://"+socket.gethostbyname(host)+":2379" for host in hostnames]

# tests = [(tag, test, failure_injection), ...]
tests = [
        ('Sequential-3S-4B', lambda client: tester.multi_client(client, endpoints[:3], 1, op_gen.sequential_keys(1000, 4)), failure.none),
        ('Sequential-3S-1KB', lambda client: tester.multi_client(client, endpoints[:3], 1, op_gen.sequential_keys(1000, 1024)), failure.none),
        ('Sequential-3S-1MB', lambda client: tester.multi_client(client, endpoints[:3], 1, op_gen.sequential_keys(100, 1048576)), failure.none)
        ]

tester.run_tests(tests)

