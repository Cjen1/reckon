import distributions.message_pb2 as msg_pb
from utils.op_gen import Operation
from os import listdir
from subprocess import call, Popen
import argparse
from threading import Thread
import socket
import time
from tqdm import tqdm 
import json
import zmq
from Queue import Queue as queue
import Queue

import importlib

client_port_id = 50000
def run_test(cluster_ips, op_obj, duration=30, num_clients=1, sys='etcd_go'):
    global client_port_id
    opprod, opbuf, prereq = op_obj
    
    service, client = sys.split('_')
    print("Running Test")
    
    # Increment client port to ensure that there is no unencapsulated state
    client_port_id = client_port_id + 1 if client_port_id < 60000 else 50000

    client_port = str(client_port_id)
    #-------------- Loop until can connect to a port --------------------------------
    while(True):
        try:
            client_port = str(client_port_id)
            socket = zmq.Context().socket(zmq.ROUTER)
            socket.bind("tcp://127.0.0.1:" + client_port)
            # socket.setsockopt(zmq.LINGER, 0)
            # Prevents infinite waits
            # socket.RCVTIMEO = 1000 * duration
            break
        except zmq.ZMQError as ex:
            print(ex)
            # Increment client port to ensure that there is no unencapsulated state
            client_port_id = client_port_id + 1 if client_port_id < 60000 else 50000

    #--------------------------------- start clients --------------------------------
    microclients = []
    for i in range(num_clients):
        path = "/mnt/main/systems/"+service+"/clients/"+client+"/client"
        print(path)
        microclients.append(start_microclient(path, client_port, cluster_ips, str(i)))

    #------------------------------ Run Test ----------------------------------------
    #--- Satisify prerequisites -------------
    print("Container: Awaiting ready signals")
    readys, _ = get_ready_signals(socket, num_clients)
    print("Sending prerequsites")
    run_ops_list(prereq, socket, readys)

    resps = []
    def store_resp_fn(resp_time, st, end, err, client_idx, op_type, target):
        resps.append([client_idx, resp_time, err, st, end, "write" if op_type else "read", target])

    fails = []
    def store_fail_fn(failure_type, start, end):
        fails.append([failure_type, start, end])

    print("Sending Operations")

    #--- NOW start producing operations. Will probably still experience slightly 
    #--- bursty start but can then move the line below if necessary.
    opprod.start()

    #send operations until time limit
    t_end = time.time() + duration
    while time.time() < t_end:
        run_ops(opbuf, socket, store_resp_fn, readys)

    
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
    for clientbridge in microclients:
        timeout = 15 # Seconds
        while clientbridge.poll() is None and timeout > 0:
            time.sleep(1)
            timeout -= 1

        if clientbridge.poll() is None:
            print("WARN: Had to kill process")
            clientbridge.kill()
        else:
            clientbridge.wait()

    socket.close()

    #----------------------- Write responses to disk --------------------------------
    print("Writing responses to disk")
    test_name = "results"
    filename = "/results.res"
    fres = open(filename, "w")
    data ={'test': test_name, 'resps': resps, 'fail': fails}
    json.dump(data, fres)

    fres.close()
    print("CONTAINER: test finished exiting")

#----- Utility Functions --------------------------------------------------------
def run_ops_list(operations, socket, ready_signals, store_resp_fn=(lambda *args: None)):
    #------- Send operations to each of the clients in a load balanced manner -------
    for operation in operations:
        # Get address to send to either from initial queue or from received responses
        addr = {}
        if len(ready_signals) > 0:
            print("CONTAINER: replying to first ready signal")
            addr = ready_signals.pop()
        else:
            addr, empty, rec = socket.recv_multipart(flags=0)
            resp = msg_pb.Response()
            resp.ParseFromString(rec)
            store_resp_fn(resp.response_time, resp.start, resp.end, resp.err, resp.optype, resp.target)

        socket.send_multipart([addr,b'',operation])

def run_ops(opbuf, socket, store_resp_fn=lambda *args:None, ready_signals=set()):
    addr = {}
    if len(ready_signals) > 0:
        addr = ready_signals.pop()
    else:
        addr, _, rec = socket.recv_multipart()
        resp = msg_pb.Response()
        resp.ParseFromString(rec)
        store_resp_fn(resp.response_time, resp.start, resp.end, resp.err, resp.clientid, resp.optype, resp.target)

    op = opbuf.get()	# If no oerations are available blocks until one is 
    
    # Reversed order because we anticipate the client to wait for the operation. 
    # With other ordering would waste time once we should be able to send the operation.

    socket.send_multipart([addr, b'', op])

# starts a microclient with given config
# port: local port for communication channel
def start_microclient(path, port, cluster_ips, client_id):
    arg_ips = cluster_ips
    print("CLIENT PATH: "+path)

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

def producer(op_gen, op_buf, rate):
    opid = 0
    start = time.time()
    while(True):
        while time.time() < start + opid * 1.0/float(rate):
            pass
        try:
            op_buf.put_nowait(op_gen())
        except Queue.Full:
            pass
        opid += 1

if __name__ == "__main__":

    #------- Parse arguments --------------------------
    parser = argparse.ArgumentParser(description='Executes the test for the benchmark.')
    parser.add_argument(
            'system',
	    help='The single system being subjected to this test.')
    parser.add_argument(
            'distribution',
            help='The distribution to generate operations from')
    parser.add_argument(
            'cluster_ips',
            help='The cluster under test')
    parser.add_argument(
            '--dist_args',
            default='None',
            help='settings for the distribution. eg. size=5,mean=10')
    parser.add_argument(
            '--benchmark_config',
            help='A comma separated list of benchmark parameters, eg. nclients=20,rate=500,failure_interval=10.')
    parser.add_argument(
            '--duration',
	    help='The duration for which to test.')
    
    args = parser.parse_args()

    system = args.system
    
    # parse arguments
    distribution = args.distribution
    if args.dist_args != 'None':
        print(args.dist_args)
        dist_args = args.dist_args.split(',')
        print(dist_args)
        dist_args = dict([arg.split('=') for arg in dist_args])
        print(dist_args)
    else:
        dist_args = {}
    op_gen_module = importlib.import_module('distributions.' + distribution)

    op_prereq = op_gen_module.generate_prereqs(**dist_args)		
    op_gen_gen = op_gen_module.generate_ops(**dist_args)		

    bench_args = dict([config.split('=') for config in args.benchmark_config.split(',')])

    duration=float(args.duration)

    # Set up buffers etc
    operation_buffer = queue(maxsize=3*bench_args['rate']) 
    # don't waste any memory after 3 seconds of not consuming ops.

    op_producer = Thread(target=producer, args=[op_gen_gen, operation_buffer, bench_args['rate']])
    op_producer.setDaemon(True)
    # Not starting yet. Otherwise might build up ops during prereq leading 
    # to overload before benchmark should really begin, which defeats 
    # the purpose of rate throttling. 

    operation_bundle = [op_producer, operation_buffer, op_prereq]

    run_test(cluster_ips=args.cluster_ips, op_obj=operation_bundle, num_clients=int(bench_args['nclients']), sys=system, duration=duration) 

