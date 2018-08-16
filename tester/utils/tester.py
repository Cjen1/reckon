from utils.op_gen import Op
from utils import link, failure, message_pb2 as msg_pb
from os import listdir
from subprocess import call, Popen
from threading import Thread
import socket
import time
from tqdm import tqdm 
import json

#---------------------------------------------------------------------------
#------------ Test running functions, config below -------------------------
#---------------------------------------------------------------------------

def start_micro_client(path, port, cluster_hostnames):
    ips = [socket.gethostbyname(host) for host in cluster_hostnames]

    arg_ips = "".join(ip + "," for ip in ips)[:-1]

    cliient = {}
    if path.endswith(".jar"):
        client = Popen(['java', '-jar', path, port, arg_ips])
    elif path.endswith(".py"):
        client = Popen(['python', path, port, arg_ips])
    else:
        client = Popen([path, port, arg_ips])

def separate(data, num_buckets):
    result = [[] for i in range(num_buckets)]

    for i, x in enumerate(data):
        result[i % num_buckets].append(x)
    print('Separated Data: ')
    print([len(i) for i in result])
    return result

def run_ops(context_generator, operations, client_id, resps_storage, logs_storage):
    print('Running operations with client ' + str(client_id))
    resps = []
    logs = []
    link_context = context_generator(50000 + client_id)

    for op in operations:
        if op.op_type == Op.type_NOP:
            time.sleep(op.time)
            continue
        print('About to send message to client ' + str(client_id) + ' at port ' + str(link_context.port))
        rec = link.send(link_context, op.operation)
	print(rec)
        resp = msg_pb.Response()
        resp.ParseFromString(rec)

        resps.append(resp.response_time)
        logs.append(resp.err)

    resps_storage[client_id] = resps
    logs_storage[client_id] = logs

    link.close(link_context)
    return

def flatten(l):
    return [item for sublist in l for item in sublist]

def run_test(test):
    tag, cluster_hostnames, num_clients, operations, failure = test

    print("Running test: " + tag)

    separated_ops = separate(operations, num_clients) 

    for client in listdir("clients"):
        service = client[:(client.index('_'))]
	
	if("zookeeper" in service):
            if( ( (service == "zookeeper") and len(cluster_hostnames) == 5) or ( (service == "zookeeper5") and len(cluster_hostnames) == 3)):
                continue

        # marshall hostnames
        arg_hostnames = "".join(host + "," for host in cluster_hostnames)[:-1]

        print("Starting cluster: " + service)
        call(["python", "scripts/" + service + "_setup.py", arg_hostnames])

        for i in range(num_clients):
            start_micro_client("clients/"+client, str(50000 + i), cluster_hostnames)

        # Set up client threads 
        resp_storage = [i for i in range(num_clients)]
        logs_storage = [i for i in range(num_clients)]
        
        gens = [lambda k : link.gen_context(k) for i in range(num_clients)]
        
        client_threads = [ Thread (
            target = run_ops,
            args = [
                gens[client_id],
                separated_ops[client_id],
                client_id,
                resp_storage,
                logs_storage
                ])
            for client_id in range(num_clients)]

        f_start, f_end = failure(service)

        print("Starting test")

        f_start()

        for thread in client_threads:
            thread.start()

        for thread in client_threads:
            thread.join()

        print("Test finished, tidying up")
        f_end()

        # Ensure that threads have run correctly
        for i in range(num_clients):
            if resp_storage[i] == i:
                print("Threads have not run correctly")
                break

        print("Writing results to file")
        resps = flatten(resp_storage)
        logs = flatten(logs_storage)

        test_name = tag + "_" + client
        fres = open("results/"+test_name+".res", "w")
        json.dump({'test': test_name, 'resps': resps, 'logs': logs}, fres)
        fres.close()
