from utils import link, failure, message_pb2 as msg_pb
from os import listdir
from subprocess import call, Popen
from threading import Thread
import socket
import time
from tqdm import tqdm 
import json
import zmq

# starts a microclient with given config
# port: local port for communication channel
def start_micro_client(path, port, cluster_hostnames):
    ips = [socket.gethostbyname(host) for host in cluster_hostnames]

    arg_ips = "".join(ip + "," for ip in ips)[:-1]

    client = {}
    if path.endswith(".jar"):
        client = Popen(['java', '-jar', path, port, arg_ips])
    elif path.endswith(".py"):
        client = Popen(['python', path, port, arg_ips])
    else:
        client = Popen([path, port, arg_ips])

# splits the given data into num_buckets buckets
def separate(data, num_buckets):
    result = [[] for i in range(num_buckets)]

    for i, x in enumerate(data):
        result[i % num_buckets].append(x)
    print('Separated Data: ')
    print([len(i) for i in result])
    return result

def run_test(test, client_port = "50000", failure_port = "50001"):
    tag, cluster_hostnames, num_clients, operations, failure = test

    print("Running test: " + tag)

    # TODO implement failure injection again

    for client in listdir("clients"):
        service = client[:(client.index('_'))]
	
        #---------------- Setup system and start clients --------------------------------
        # Ensure that the correct zookeeper system is being run
	if("zookeeper" in service) and not (
            (service == "zookeeper"  and len(cluster_hostnames) == 3) or 
            (service == "zookeeper5" and len(cluster_hostnames) == 5)):
                continue

        # marshall hostnames
        arg_hostnames = "".join(host + "," for host in cluster_hostnames)[:-1]

        print("Starting cluster: " + service)
        call(["python", "scripts/" + service + "_setup.py", arg_hostnames])

        for i in range(num_clients):
            start_micro_client("clients/"+client, client_port, cluster_hostnames)

        socket = zmq.Context().socket(zmq.ROUTER)
        socket.bind("tcp://127.0.0.1:" + client_port)

        #------------------ Recieve ready signals from clients --------------------------
        addresses = set()
        for i in tqdm(range(num_clients), desc="Ready signals"):
            address, empty, ready = socket.recv_multipart()
            addresses.add(address)

        #------------------- Send initial operation to each client ----------------------
        for addr in addresses:
            operation = operations.pop(0)
            socket.send_multipart([
                addr,
                b'',
                operation
                ]) 
        #------- Send operations to each of the clients in a loda balanced manner -------
        resps = []
        logs = []
        for operation in tqdm(operations, desc="Sending Operations"):
            address, empty, rec = socket.recv_multipart()
            socket.send_multipart([
                address,
                b'',
                operation
                ])

            resp = msg_pb.Response()
            resp.ParseFromString(rec)

            resps.append([address, resp.response_time])
            logs.append([address, resp.err])

        #---------- Collect remaining responses and make clients quit cleanly -----------
        print()
        quit_op = msg_pb.Operation()
        quit_op.quit.msg = "Quitting normally"
        quit_op = quit_op.SerializeToString()
        for i in tqdm(range(num_clients), desc="Closing clients"):
            address, empty, rec = socket.recv_multipart()
            # Collect remaining responses 
            if rec != b'':
                resp = msg_pb.Response()
                resp.ParseFromString(rec)

                resps.append([addresss, resp.response_time])
                logs.append([address, resp.err])

            # Send quit message
            socket.send_multipart([
                address,
                b'',
                quit_op
                ])

        socket.close()

        #----------------------- Write responses to disk --------------------------------
        print("Writing responses to disk")
        test_name = tag + "_" + client
        fres = open("results/" + test_name + ".res", "w")
        json.dump({'test': test_name, 'resps': resps, 'logs': logs}, fres)
        fres.close()
