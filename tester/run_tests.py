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

# tests = [(tag, test, hostnames, failure_injection), ...]
tests = [
        ('Sequential-3S-4B', 
            lambda client: tester.multi_client(client, endpoints[:3], 1, op_gen.sequential_keys(10000, 4)), 
            hostnames[:3], failure.crash(0.5, 0.1, endpoints[:3])),
        ('Sequential-3S-4B', 
            lambda client: tester.multi_client(client, endpoints[:3], 1, op_gen.sequential_keys(10000, 4)),
            hostnames[:3], failure.crash(1, 0.1, endpoints[:3]))
        ]

tester.run_tests(tests)

