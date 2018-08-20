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
def start_microclient(path, port, cluster_hostnames, client_id):
    ips = [socket.gethostbyname(host) for host in cluster_hostnames]

    arg_ips = "".join(ip + "," for ip in ips)[:-1]

    client = {}
    if path.endswith(".jar"):
        client = Popen(['java', '-jar', path, port, arg_ips, client_id])
    elif path.endswith(".py"):
        client = Popen(['python', path, port, arg_ips, client_id])
    else:
        client = Popen([path, port, arg_ips, client_id])

    return client

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

        microclients = []
        for i in range(num_clients):
            microclients.append(start_microclient("clients/"+client, client_port, cluster_hostnames, str(i)))

        socket = zmq.Context().socket(zmq.ROUTER)
        socket.bind("tcp://127.0.0.1:" + client_port)

        #------------------ Recieve ready signals from clients --------------------------
        addr_init_ops = set()
        for i in tqdm(range(num_clients), desc="Ready signals"):
            address, empty, ready = socket.recv_multipart()
            addr_init_ops.add(address)

        #------------------- Send initial operation to each client ----------------------
        for addr in addr_init_ops:
            operation = operations.pop(0)
            socket.send_multipart([
                addr,
                b'',
                operation
                ]) 

        #------- Send operations to each of the clients in a loda balanced manner -------
        resps = [] 
        logs = []
        def store_resp(resp_time, st, end, err, client_idx):
            resps.append([client_idx, resp.response_time, st, end])
            logs.append([client_idx, err, st, end])

        for operation in tqdm(operations, desc="Sending Operations"):
            address, empty, rec = socket.recv_multipart()
            socket.send_multipart([
                address,
                b'',
                operation
                ])

            resp = msg_pb.Response()
            resp.ParseFromString(rec)

            store_resp(resp.response_time, resp.start, resp.end, resp.err, resp.id)

        #---------- Collect remaining responses and make clients quit cleanly -----------
        quit_op = msg_pb.Operation()
        quit_op.quit.msg = "Quitting normally"
        quit_op = quit_op.SerializeToString()
        for i in tqdm(range(num_clients), desc="Closing clients"):
            address, empty, rec = socket.recv_multipart()
            # Collect remaining responses 
            resp = msg_pb.Response()
            try:
                resp.ParseFromString(rec)
            except google.protobuf.message.DecodeError:
                print(rec)

            store_resp(resp.response_time, resp.start, resp.end, resp.err, resp.id)

            # Send quit message
            socket.send_multipart([
                address,
                b'',
                quit_op
                ])

        print("Waiting for clients to quit")
        for microclient in microclients:
            microclient.wait()
            

        socket.close()

        #----------------------- Write responses to disk --------------------------------
        print("Writing responses to disk")
        test_name = tag + "_" + client
        filename = "results/" + test_name + ".res"
        fres = open(filename, "w")
        data ={'test': test_name, 'resps': resps, 'logs': logs}
        json.dump(data, fres)

        fres.close()
