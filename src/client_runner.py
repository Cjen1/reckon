from multiprocessing import Pool, Manager, Queue, Value
from subprocess import Popen
from threading import Thread
import time
import sys
import os
import json
import zmq
import random

import logging

from Queue import Empty as QEmpty, Full as QFull
from src.utils.req_factory import ReqFactory
import src.utils.message_pb2 as msg_pb
import select

import importlib

from struct import pack, unpack

from tqdm import tqdm


def send(client, op):
    in_pipe, out_pipe = client
    size = pack("<l", op.ByteSize())  # little endian signed long (4 bytes)
    payload = op.SerializeToString()
    in_pipe.write(size + payload)


def read_exactly(fd, size):
    return fd.read(size)


def read_packet(pipe):
    size = read_exactly(pipe, 4)
    if size:
        size = unpack("<l", size)  # little endian signed long (4 bytes)
        # unpack returns a tuple even if a single value
        payload = read_exactly(pipe, size[0])
        return payload
    else:
        return None


def read_payload(pipe):
    payload = read_packet(pipe)
    if payload:
        resp = msg_pb.Response()
        resp.ParseFromString(payload)
        return resp
    else:
        logging.debug("Got nothing from pipe, probably EOF")
        return None


def preload(ops_provider, clients, duration, rate):
    logging.debug("PRELOAD")

    for prereq in ops_provider.prereqs:
        send(random.choice(clients), prereq)

    sim_t = 0
    period = 1 / rate
    with tqdm(total=duration) as pbar:
        while sim_t < duration:
            op = ops_provider.get_ops(sim_t)
            # logging.debug("Sending op")
            send(random.choice(clients), op)
            sim_t = sim_t + period
            pbar.update(period)


def ready(clients):
    logging.debug("READY")

    for client in clients:
        send(client, ReqFactory.finalise())

    pipes = [result_pipe for in_pipe, result_pipe in clients]

    def recv_one():
        logging.debug(pipes)
        readable, _, execeptional = select.select(pipes, [], pipes)
        logging.debug("CR: received at least one: ")
        return read_packet(readable[0])

    logging.debug("Waiting to receive readys")
    for client in clients:
        recv_one()


def execute(clients, failures, duration):
    logging.debug("EXECUTE")

    start_time = time.time()

    for client in clients:
        logging.debug("Sending start msg")
        send(client, ReqFactory.start())

    null_failure = lambda *args, **kwargs: None
    failures = failures + [null_failure]
    n_failures = len(failures)
    sleep_time = duration / (n_failures)

    failure_times = [(i + 1) * sleep_time + start_time for i, _ in enumerate(failures)]

    for failure_time, failure in zip(failure_times, failures):
        sleep_time = failure_time - time.time()
        logging.debug("BENCHMARK: sleeping for" + str(sleep_time))
        sys.stdout.flush()
        if sleep_time > 0:
            time.sleep(sleep_time)
        failure()


def collate(pipes, test_results_location, total):
    logging.debug("COLLATE")
    resps = []
    inputs = pipes

    with tqdm() as pbar:
        while inputs:
            readable, _, _ = select.select(pipes, [], pipes)
            for pipe in readable:
                resp = read_payload(pipe)
                if not resp:  # resp = None
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
                            "Op_type": resp.optype,
                        }
                    )
                    pbar.update(1)

    logging.debug("COLLATE: done, writing: " + test_results_location)
    with open(test_results_location, "w") as fres:
        json.dump(resps, fres)

    logging.debug("COLLATE: written to file")


def run_test(
    test_results_location,
    clients,
    ops_provider,
    rate,
    duration,
    system,
    cluster,
    failures,
):
    rate = float(rate)
    duration = int(duration)

    logging.debug("Setting up microclients")
    sys.stdout.flush()
    microclients = [
        system.start_client(client, client_id, cluster)
        for client_id, client in enumerate(clients)
    ]
    logging.debug("Microclients started")

    preload(ops_provider, microclients, duration, rate)
    ready(microclients)

    t_collate = Thread(
        target=collate,
        args=[
            [out_pipe for (in_pipe, out_pipe) in microclients],
            test_results_location,
            rate * duration,
        ],
    )
    t_collate.daemon = True
    t_collate.start()

    execute(microclients, failures, duration)

    logging.debug("Waiting to join collate thread")
    t_collate.join()
