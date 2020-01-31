from multiprocessing import Pool, Manager, Queue, Semaphore, Value
from subprocess import Popen, PIPE
from threading import Thread
import time
import sys
from ctypes import c_bool
import os
import json
import zmq
import cgroups
import random

from Queue import Empty as QEmpty, Full as QFull
import src.utils.message_pb2 as msg_pb

import importlib

from struct import pack

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
stop_flag = None

def clean_address(address):
    try:
        os.unlink(address)
    except OSError:
        if os.path.exists(address):
            raise

def run_prereqs(socket, send, clients, operations):
    for operation in operations:
        _ = socket.recv_multipart()
        send(random.choice(clients), operation)

def setup_socket(config):
    socket = zmq.Context().socket(zmq.DEALER)

    runner_address = "ipc://"+config['runner_address']
    clean_address(runner_address)

    socket.setsockopt(zmq.LINGER, 0)
    socket.RCVTIMEO = 60*60*1000 #1000 * config['duration'] 

    os.umask(0o000)
    socket.bind(runner_address)
    return socket

def recv_loop(socket, config):
    resps = []
    while(not stop_flag.value):
        if socket.poll(5000, zmq.POLLIN):
            recv = socket.recv(zmq.NOBLOCK)
            print("received output")
            sys.stdout.flush()
            resp = msg_pb.Response()
            resp.ParseFromString(recv)
            resps.append(
                    {
                        "Resp_time": resp.response_time,
                        "Cli_start": resp.client_start,
                        "Q_start": resp.queue_start,
                        "End": resp.end,
                        "Client_id": resp.clientid,
                        "Error": resp.err,
                        "Target": resp.target,
                        "Op_type": resp.optype
                        }
                    )

    with open(config['f_dest'], "w") as fres:
        json.dump(resps, fres)

def setup_start_test(mnclients, config):
    print("Setting up microclients")
    sys.stdout.flush()
    microclients = [
            config['start_client'](mnclient, client_id, config)
            for client_id, mnclient in enumerate(mnclients)
            ]

    def send(client, op):
        cli = client
        size = pack('<L',op.ByteSize())
        cli.stdin.write(size)
        payload = op.SerializeToString()
        cli.stdin.write(payload)

    print("Configuring socket")
    sys.stdout.flush()
    socket = setup_socket(config)
    print("CR: Running prereqs")
    sys.stdout.flush()
    run_prereqs(socket, send, microclients, config['op_prereq'])

    t_recv = Thread(target=recv_loop, args=[socket, config])
    t_recv.daemon = True
    t_recv.start()

    barrier.wait()

    start = time.time()
    end = start + config['duration']

    rate = float(config['rate'])
    op_gen = config['op_gen']

    opid = 0
    while(time.time() < end):
        #Busy wait until time for op
        while time.time() < start + opid * 1.0/rate:
            pass
        opid = opid + 1
        print("sending")
        sys.stdout.flush()
        send(random.choice(microclients), op_gen())

    print("CR: Finished")
    sys.stdout.flush()
    stop_flag.value = True

    print("CR: Sending quit operations")
    sys.stdout.flush()
    quit_op = msg_pb.Operation()
    quit_op.quit.msg = "Quitting normally"
    for client in microclients:
        send(client, quit_op)

    print("CR: Waiting for receive loop to join")
    sys.stdout.flush()
    t_recv.join()

def run_test(f_dest, clients, ops, rate, duration, service_name, client_name, ips, failures):
    rate = float(rate)
    duration = int(duration)
    op_prereq, op_gen = ops
    config = {
        'service':service_name,
        'client':client_name,
        'cluster_ips': ips,
        'duration': duration,
        'op_prereq': op_prereq,
        'op_gen': op_gen,
        'rate': rate,
        'runner_address': os.getcwd() + '/src/utils/sockets/benchmark.sock', # needs to be relative to the current environment rather than to a host
        'client_address': os.getcwd() + '/src/utils/sockets/benchmark.sock', # needs to be relative to the current environment rather than to a host
        'start_client': (importlib.import_module('systems.%s.scripts.client_start' % service_name).start),
        'f_dest': f_dest
        }

    print("RUNNER ADDRESS: "+ config['runner_address'])
    sys.stdout.flush()

    #Set up multiprocessing primitives
    m = Manager()
    global stop_flag
    stop_flag = m.Value(c_bool, False)
    global barrier
    barrier = Barrier(m, 2) # one for failures, one for generator

    t_test = Thread(target=setup_start_test, args = [clients, config])
    t_test.daemon = True
    t_test.start()

    barrier.wait()

    sleepTime = duration / (len(failures) + 1)
    for failure in (failures+[(lambda*args, **kwargs:None)]):
        print("BENCHMARK: sleeping for" + str(sleepTime))
        sys.stdout.flush()
        time.sleep(sleepTime)
        failure()

    t_test.join()
