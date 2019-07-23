from multiprocessing import Pool, Manager, Queue, Semaphore, Value
from subprocess import Popen, PIPE
from threading import Thread
import time
import sys
from ctypes import c_bool
import os
import json
import zmq

from Queue import Empty as QEmpty, Full as QFull
import distributions.message_pb2 as msg_pb

class Barrier:
    def __init__(self, m, n):
        self.n = n
        self.count = m.Value('i', 0)
        self.mutex = m.Semaphore(1)
        self.bar = m.Semaphore(0)

    def wait(self):
        self.mutex.acquire()
        self.count.value += 1
        self.mutex.release()

        if self.count.value == self.n:
            self.bar.release()

        self.bar.acquire()
        self.bar.release()

barrier = {}
req_queue = {}
res_queue = {}
config = {}
stop_flag = None

def clean_address(address):
    try:
        os.unlink(address)
    except OSError:
        if os.path.exists(address):
            raise

def run_prereqs(socket, operations):
    for operation in operations:
        addr, _, _ = socket.recv_multipart()
        socket.send_multipart([addr, b'', operation])
        

def run_client(clients, config):
    #--- Setup ----------
    client_address = "ipc:///tmp/benchmark.sock"
    clean_address(client_address)

    socket = zmq.Context().socket(zmq.ROUTER)
    socket.bind(client_address)
    socket.setsockopt(zmq.LINGER, 0)
    #Prevent infinite waiting timeout is in milliseconds
    socket.RCVTIMEO = 1000 * config['duration'] 
    
    client_path = "systems/"+config['service']+"/clients/"+config['client']+"/client"
    cmd = []
    if client_path.endswith(".jar"):
        cmd = ['java', '-jar']
    elif client_path.endswith(".py"):
        cmd = ['python']
    arg_ips = "".join(ip + "," for ip in config['cluster_ips'])[:-1]

    microclients = [
            client.popen(
                cmd + [client_path, arg_ips, str(client_id), client_address],
                stdout = sys.stdout, stderr=sys.stderr, close_fds = True
                )
            for client_id, client in enumerate(clients)
            ]

    run_prereqs(socket, config['op_prereq'])

    # Recieve ready signals from microclients
    readys = [addr for addr, _, _ in [socket.recv_multipart() for client in clients]]

    #wait for all other clients to finish setup
    barrier.wait()

    def send(addr):
        op = req_queue.get(timeout=2/config['rate'])
        socket.send_multipart([addr, b'', op])

    def recv():
        addr, _, res = socket.recv_multipart()
        res_queue.put_nowait(res)
        return addr

    #-- Start Test ------

    # Use up readys to allow for tight test loop with no startup
    for ready in readys:
        # If short duration may not get through all readys before timeout, thus block on producer
        try:
            send(ready)
        except QEmpty:
            pass

    while(not stop_flag.value): 
        try:
            addr = recv()
            send(addr)
        except QEmpty:
            pass

    quit_op = msg_pb.Operation()
    quit_op.quit.msg = "Quitting normally"
    quit_op = quit_op.SerializeToString()
    for ready in readys:
        addr, _, _ = socket.recv_multipart()
        socket.send_multipart([addr, b'', quit_op])

def producer(op_gen, rate, duration, stop_flag):
    print("Producer: Waiting")
    barrier.wait()
    print("Starting producing ops")
    opid = 0
    start = time.time()
    end = start+duration
    while(time.time() < end):
        while time.time() < start + opid * 1.0/float(rate):
            pass
        req_queue.put_nowait(op_gen())
        #print("Putting op, current count: ", (req_queue.qsize()))
        opid += 1

    stop_flag.value = True
    #print("stopped: {0}s later".format(time.time() - start))
    

def run_test(clients, ops, rate, duration, service_name, client_name, ips):
    rate = float(rate)
    duration = int(duration)
    op_prereq, op_gen = ops
    config = {
        'service':service_name,
        'client':client_name,
        'cluster_ips': ips,
        'duration': duration,
        'op_prereq': op_prereq,
        'rate': rate
        }

    #Set up multiprocessing primitives
    m = Manager()
    global barrier
    barrier = Barrier(m, 2) # one for each client, 1 for producer
    global res_queue
    res_queue = m.Queue()
    global req_queue
    req_queue = m.Queue()
    global cluster_ips
    cluster_ips = ips
    global stop_flag
    stop_flag = m.Value(c_bool, False)

    op_producer = Thread(target=producer, args=[op_gen, rate, duration, stop_flag])

    #pool = Pool(processes=len(clients))
    #pool.map(run_client, zip(clients, range(len(clients))))

    #pool.close()

    mc = Thread(target=run_client, args=[clients, config]) 
    mc.start()

    op_producer.start()
    op_producer.join()

    print("waiting for microclients to finish")
    mc.join()

    resps = []
    while(not res_queue.empty()):
        rec = res_queue.get()
        resp = msg_pb.Response()
        resp.ParseFromString(rec)
        resps.append(resp)
    resps = [
                [
                    resp.response_time,
                    resp.start,
                    resp.end,
                    resp.clientid,
                    resp.err,
                    resp.target,
                    resp.optype
                ]
            for resp in resps 
            ]
    #print("RESPS: ", resps)

    with open("../results/{0}_{1}.res".format(service_name, client_name), "w") as fres:
        json.dump(resps, fres)


#if __name__ == '__main__':
#    from mininet.net import Mininet
#    from mininet.topolib import TreeTopo
#    tree = TreeTopo(depth=2,fanout=2)
#    net = Mininet(topo=tree)
#    net.start()
#    clients = [net.hosts[0]]
#
#    import distributions.uniform as uni
#    ops = uni.generate_ops()
#
#    t=Thread(target=run_test, args=[clients, ops, 1, 10, "template", "go", ["1.0.0.1, 10.0.0.2"]])
#
#    t.start()
#    t.join()
