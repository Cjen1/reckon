from op_gen import op_gen, link
from os import listdir
import subprocess
import json


def run_tests():
    tests = [
            ('Sequential-4B', lambda : op_gen.sequential_keys(4444, 100, 4))
            ]

    clients = listdir("clients")
    client_execs = ["clients/" + cl for cl in clients]

    for tag, test in tests:
        print("Test: " + tag)
        for name, path in zip(clients, client_execs):
            print(" Client: " + name)

            client = {}
            if path.endswith(".jar"):
                client = subprocess.Popen(['java', '-jar', path])
            else:
                client = subprocess.Popen(path)

            # execute test
            data = test()
            
            result_path = "./results/{0}:{1}.res".format(tag, name)
            with open(result_path, "w") as fres:
                json.dump(("{}-{}".format(tag, name), data), fres)

run_tests()
