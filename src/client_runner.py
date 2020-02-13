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
import select

import importlib

from struct import pack, unpack

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

def send(client, op):
    in_pipe, out_pipe = client
    size = pack('<L',op.ByteSize())
    payload = op.SerializeToString()
    in_pipe.write(size+payload)

def read_packet(pipe):
    print(pipe)
    size = os.read(pipe, 4)
    print(size.encode('hex'))
    if size:
        size = unpack('<L', size) 
        print(size)
        # unpack returns a tuple even if a single value
        payload = os.read(pipe,size[0])
        return payload
    else:
        return None

def read_payload(pipe):
    payload = read_packet(pipe)
    if payload:
        resp = msg_pb.Response()
        resp.ParseFromString(payload)
        print("CR: Read from pipe successfully")
        return resp 
    else:
        return None

def recv_loop(pipes, config):
    resps = []
    inputs = pipes
    while inputs:
        readable, _, _ = select.select(pipes, [], pipes)
        for pipe in readable:
            resp = read_payload(pipe)
            if not resp: # resp = None
                inputs.remove(pipe)
            else:
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

def run_prereqs(clients, operations):
    for operation in operations:
        send(random.choice(clients), operation)

def wait_for_readys(n, pipes):
    print("CR: waiting for readys")
    def recv_one(): 
        readable, _, execeptional = select.select(pipes, [], pipes)
        print("CR: received at least one: ")
        print(readable)
        return read_packet(readable[0])
    for _ in range(n):
        recv_one()

def receive_readys_and_prereqs(clients, prereqs):
    run_prereqs(clients, prereqs)
    wait_for_readys(len(clients) + len(prereqs), [out_pipe for (in_pipe, out_pipe) in clients])

def setup_start_test(mnclients, config):
    print("Setting up microclients")
    sys.stdout.flush()
    microclients = [
            config['start_client'](mnclient, client_id, config)
            for client_id, mnclient in enumerate(mnclients)
            ]


    print("Configuring socket")
    sys.stdout.flush()
    print("CR: Running prereqs")
    sys.stdout.flush()

    receive_readys_and_prereqs(microclients, config['op_prereq'])

    t_recv = Thread(target=recv_loop, args=[[out_pipe for (in_pipe, out_pipe) in microclients], config])
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
        send(random.choice(microclients), op_gen())

    print("CR: Finished, awaiting results")
    sys.stdout.flush()

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
