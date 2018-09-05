from utils import link, failure, message_pb2 as msg_pb
from utils.op_gen import Operation
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

def run_ops(operations, socket, num_clients, service, store_resp_fn=(lambda *args: None), store_fail_fn=(lambda *args: None)):
    if len(operations) < 1:
        return

    #------------------ Recieve ready signals from clients --------------------------
    addr_init_ops = set()
    for i in tqdm(range(num_clients), desc="Ready signals"):
        address, empty, ready = socket.recv_multipart()
        addr_init_ops.add(address)

    #------- Send operations to each of the clients in a load balanced manner -------

    for operation in tqdm(operations, desc="Sending Operations"):
        if operation.type == Operation.STANDARD:
            # Get address to send to either from initial queue or from received responses
            addr = {}
            if len(addr_init_ops) > 0:
                addr = addr_init_ops.pop()
            else:
                addr, empty, rec = socket.recv_multipart()
                resp = msg_pb.Response()
                resp.ParseFromString(rec)
                store_resp_fn(resp.response_time, resp.start, resp.end, resp.err, resp.id)

            socket.send_multipart([addr,b'',operation.op])

        elif operation.type == Operation.SYSTEMFAILURE:
            opThread = Thread(target = operation.fn, args=[service, store_fail_fn])
            opThread.start()
        elif operation.type == Operation.SYSTEMRECOVERY:
            opThread = Thread(target = operation.fn, args=[service, store_fail_fn])
            opThread.start()
        else:
            print("UNKNOWN OPERATION")

client_port_id = 50000
def run_test(test):
    global client_port_id
    tag, cluster_hostnames, num_clients, op_obj, fail_fn = test
    ops, prereq = op_obj


    # Apply failure to the operations
    prereq = failure.NoFailure(prereq)
    ops = fail_fn(ops)

    print("Running test: " + tag)

    for client in listdir("clients"):
        # Increment client port to ensure that there is no unencapsulated state
        client_port_id = client_port_id + 1 if client_port_id < 60000 else 50000

        client_port = str(client_port_id)
        #-------------- Loop until can connect to a port --------------------------------
        while(True):
            try:
                client_port = str(client_port_id)
                socket = zmq.Context().socket(zmq.ROUTER)
                socket.bind("tcp://127.0.0.1:" + client_port)
                socket.setsockopt(zmq.LINGER, 0)
                break
            except zmq.ZMQError as ex:
                print(ex)
                # Increment client port to ensure that there is no unencapsulated state
                client_port_id = client_port_id + 1 if client_port_id < 60000 else 50000

        
        service = client[:(client.index('_'))]
	
        #---------------- Setup system and start clients --------------------------------
        # Ensure that the correct zookeeper system is being run

        # Sleep to allow cleanup of the zmq socket
        time.sleep(0.5)

        arg_hostnames = "".join(host + "," for host in cluster_hostnames)[:-1]
        print("Starting cluster: " + service)
        call(["python", "scripts/" + service + "_setup.py", arg_hostnames])

        microclients = []
        for i in range(num_clients):
            microclients.append(start_microclient("clients/"+client, client_port, cluster_hostnames, str(i)))

        #----------- Satisify Prerequisites and then store responses to queries ---------
        resps = [] 
        logs = []
        def store_resp(resp_time, st, end, err, client_idx):
            resps.append([client_idx, resp_time, st, end])
            logs.append([client_idx, err, st, end])

        failures = []
        def store_fail(fail_type, start, end):
            failures.append([fail_type, start, end])
        

        run_ops(prereq, socket, num_clients, service)
        run_ops(ops, socket, num_clients, service, store_resp_fn = store_resp, store_fail_fn = store_fail)

        #---------- Collect remaining responses and make clients quit cleanly -----------
        quit_op = msg_pb.Operation()
        quit_op.quit.msg = "Quitting normally"
        quit_op = quit_op.SerializeToString()
        for i in tqdm(range(num_clients), desc="Awaiting Resps & Closing clients"):
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
        data ={'test': test_name, 'resps': resps, 'logs': logs, 'fail': failures}
        json.dump(data, fres)

        fres.close()

        arg_hostnames = "".join(host + "," for host in cluster_hostnames)[:-1]
        print("Stopping cluster: " + service)
        call(["python", "scripts/" + service + "_cleanup.py", arg_hostnames])
