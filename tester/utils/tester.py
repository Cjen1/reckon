from utils import op_gen, link, failure, message_pb2 as msg_pb
from utils.op_gen import Op
from os import listdir
from  subprocess import Popen, PIPE
import json
import time
from threading import Thread
from tqdm import tqdm
import socket

def run_test(setup, operations, result, client_name):
    resps = []
    logs = []
    link_context = setup()
    for op in tqdm(operations, desc=client_name):
        if op.op_type == Op.type_NOP:
            time.sleep(op.time)
            continue

        rec = link.send(link_context, op.operation)
        resp = msg_pb.Response()
        resp.ParseFromString(rec)

        resps.append(resp.response_time)
        logs.append(resp.err)

    result(resps, logs)

def update(result, resp_time, log, i):
    result[i] = (resp_time, log)

def multi_client(client_path, endpoints, num_clients, operations):
    client_ops = [[] for i in range(num_clients)]

    for i, op in enumerate(operations):
        client_ops[i % num_clients].append(op)

    result = [i for i in range(num_clients)]

    threads = [ Thread(
        target = run_test,
        args = [
            lambda: link.gen_context(50000 + i),
            client_ops[i],
            lambda resp_time, log: update(result, resp_time, log, i),
            client_path
            ]) for i in range(num_clients)]

    print("Starting client on: " + client_path) 
    for i in range(num_clients):
        client = {}
        if client_path.endswith(".jar"):
            client = Popen(['java', '-jar', client_path, str(50000 + i), "".join(endpoint + "," for endpoint in endpoints)[:-1]])
        elif client_path.endswith(".py"):
            client = Popen(['python', client_path, str(50000 + i), "".join(endpoint + "," for endpoint in endpoints)[:-1]])
        else:
            client = Popen([client_path, str(50000 + i), "".join(endpoint + "," for endpoint in endpoints)[:-1]])

    # start all threads and then wait from them to finish
    for t in threads:
        t.start()

    for thread in threads:
        thread.join()


    # collate results from all threads
    res = []
    logs = []
    for resps, log in result:
        res.extend(resps)
        logs.extend(log)

    return (res, logs)     
        
def run_tests(tests):
    clients = listdir("clients")
    client_execs = ["clients/" + cl for cl in clients]

    for tag, test, failure in tests:
        f_start, f_end = failure
        print("Test: " + tag)
        for name, path in zip(clients, client_execs):
            killer_thread = f_start(name)

            # execute test
            data, logs  = test(path)

            result_path = "./results/{0}:{1}.res".format(tag, name)
            with open(result_path, "w") as fres:
                json.dump(["{}-{}".format(tag, name), data], fres)
            result_path = "./results/{0}:{1}.log".format(tag, name)
            with open(result_path, "w") as fres:
                json.dump(["{}-{}".format(tag, name), logs], fres)

            killer_thread.























