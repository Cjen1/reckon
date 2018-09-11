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

def run_ops_list(operations, socket, ready_signals, service, store_resp_fn=(lambda *args: None)):
    #------- Send operations to each of the clients in a load balanced manner -------
    for operation in operations:
        # Get address to send to either from initial queue or from received responses
        addr = {}
        if len(ready_signals) > 0:
            addr = ready_signals.pop()
        else:
            addr, empty, rec = socket.recv_multipart()
            resp = msg_pb.Response()
            resp.ParseFromString(rec)
            store_resp_fn(resp.response_time, resp.start, resp.end, resp.err, resp.id)

        socket.send_multipart([addr,b'',operation])

client_port_id = 50000
def run_test(test):
    global client_port_id
    tag, cluster_hostnames, num_clients, op_obj, duration, failures = test
    opgen, prereq = op_obj

    print("Running test: " + tag)

    for client in listdir("clients"):
        service = client[:(client.index('_'))]

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
                # Prevents infinite waits
                socket.RCVTIMEO = 1000 * duration
                break
            except zmq.ZMQError as ex:
                print(ex)
                # Increment client port to ensure that there is no unencapsulated state
                client_port_id = client_port_id + 1 if client_port_id < 60000 else 50000

        #---------------- Setup system and start clients --------------------------------
        # Ensure that the correct zookeeper system is being run

        #[:-1] removes the trailing ','
        arg_hostnames = "".join(host + "," for host in cluster_hostnames)[:-1]
        print("Starting cluster: " + service)
        call(["python", "scripts/" + service + "_setup.py", arg_hostnames])

        microclients = []
        for i in range(num_clients):
            microclients.append(start_microclient("clients/"+client, client_port, cluster_hostnames, str(i)))

        #------------------------------ Run Test ----------------------------------------
        #--- Satisify prerequisites -------------
        readys, _ = get_ready_signals(socket, num_clients)
        run_ops_list(prereq, socket, readys, service)

        resps = []
        logs  = []
        def store_resp_fn(resp_time, st, end, err, client_idx):
            resps.append([client_idx, resp_time, st, end])
            logs.append([client_idx, err, st, end])

        fails = []
        def store_fail_fn(failure_type, start, end):
            fails.append([failure_type, start, end])

        print("Sending Operations")
        for failure_type, failure_fn in failures:
            print("Section: " + failure_type)
            fail_thread = Thread(target = failure_fn, args=[service, store_fail_fn])
            fail_thread.start()

            #send operations to probe failure transition
            while fail_thread.isAlive():
                run_ops(opgen, socket, store_resp_fn, readys)

            #send operations until time limit
            t_end = time.time() + duration
            while time.time() < t_end:
                run_ops(opgen, socket, store_resp_fn, readys)

        
        #---------- Collect remaining responses and make clients quit cleanly -----------
        # Don't store responses since they happened out of the timeframe
        quit_op = msg_pb.Operation()
        quit_op.quit.msg = "Quitting normally"
        quit_op = quit_op.SerializeToString()
        for i in range(num_clients):
            address, _, rec = socket.recv_multipart()
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
        data ={'test': test_name, 'resps': resps, 'logs': logs, 'fail': fails}
        json.dump(data, fres)

        fres.close()

        arg_hostnames = "".join(host + "," for host in cluster_hostnames)[:-1]
        print("Stopping cluster: " + service)
        call(["python", "scripts/" + service + "_cleanup.py", arg_hostnames])

#----- Utility Functions --------------------------------------------------------
def run_ops(opgen, socket, store_resp_fn=lambda *args:None, ready_signals=set()):
    op = opgen()

    addr = {}
    if len(ready_signals) > 0:
        addr = ready_signals.pop()
    else:
        addr, _, rec = socket.recv_multipart()
        resp = msg_pb.Response()
        resp.ParseFromString(rec)
        store_resp_fn(resp.response_time, resp.start, resp.end, resp.err, resp.id)
    socket.send_multipart([addr, b'', op])

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

def get_ready_signals(socket, num_clients):
    addr_init_ops = set()
    readys = []
    for i in tqdm(range(num_clients), desc="Ready signals"):
        address, _, ready = socket.recv_multipart()
        addr_init_ops.add(address)

    return (addr_init_ops, readys)
