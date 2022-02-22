import logging
from threading import Thread
import time
import sys
import selectors 

from typing import List, cast
import src.reckon_types as t

from tqdm import tqdm

def preload(ops_provider : t.AbstractWorkload, duration) -> int:
    logging.debug("PRELOAD: begin")

    for client, op  in ops_provider.prerequisites:
        client.send(t.preload(prereq=True, operation=op))

    sim_t = 0
    total_reqs = 0
    with tqdm(total=duration) as pbar:
        for client, op in ops_provider.workload(): 
            if op.time > duration:
                break

            total_reqs += 1
            client.send(t.preload(prereq=False, operation=op))

            pbar.update(op.time - sim_t)
            sim_t = op.time
    
    for client in ops_provider.clients:
        client.send(t.finalise())
    
    logging.debug("PRELOAD: end")
    return total_reqs

def ready(clients: List[t.Client]):
    logging.debug("READY: begin")

    sel = selectors.DefaultSelector()

    for i,cli in enumerate(clients):
        cli.register_selector(sel, selectors.EVENT_READ, i)

    for _ in range(len(clients)):
        i = sel.select()[0][0].data
        
        msg = clients[i].recv()
        assert(msg.kind == t.MessageKind.Ready)
    
    logging.debug("READY: end")

def execute(clients: List[t.Client], failures: List[t.AbstractFault], duration: float):
    logging.debug("EXECUTE: begin")

    failures = failures + [t.NullFault()]
    n_failures = len(failures)
    sleep_time = duration / (n_failures)

    start_time = time.time()

    failure_times = [(i + 1) * sleep_time + start_time for i, _ in enumerate(failures)]

    for client in clients:
        client.send(t.start())

    for failure_time, failure in tqdm(zip(failure_times, failures), desc = "failure execution"):
        sleep_time : float = failure_time - time.time()
        sys.stdout.flush()
        if sleep_time > 0:
            time.sleep(sleep_time)
        failure.apply_fault()

    logging.debug("EXECUTE: end")

def collate(clients: List[t.Client], test_results_location: str, total_reqs: int):
    logging.debug("COLLATE: begin")

    sel = selectors.DefaultSelector();

    for i, client in enumerate(clients):
        client.register_selector(sel, selectors.EVENT_READ, i)

    resps = t.Results(responses=[])
    remaining_clients = len(clients)
    with tqdm(total=total_reqs) as pbar:
        while remaining_clients > 0:
            i = sel.select()[0][0].data
            msg = clients[i].recv()
            if msg.kind == t.MessageKind.Finished:
                remaining_clients -= 1
                clients[i].unregister_selector(sel, selectors.EVENT_READ)
            elif msg.kind == t.MessageKind.Result:
                pbar.update(1)
                payload = cast(t.Result, msg.payload)
                resps.responses.append(payload)

    logging.debug(f"COLLATE: received, writing to {test_results_location}")
    with open(test_results_location, "w") as fres:
        fres.write(resps.json())
    logging.debug("COLLATE: end")

def run_test(
        test_results_location: str,
        clients: List[t.MininetHost],
        ops_provider: t.AbstractWorkload,
        duration: int,
        system: t.AbstractSystem,
        cluster: List[t.MininetHost],
        failures: List[t.AbstractFault],
    ):
    duration = int(duration)

    logging.debug("Setting up clients")
    sys.stdout.flush()
    clients = [
        system.start_client(client, client_id, cluster)
        for client_id, client in enumerate(clients)
    ]
    logging.debug("Microclients started")

    total_reqs = preload(ops_provider, clients)
    ready(clients)

    t_collate = Thread(
        target=collate,
        args=[
            clients,
            test_results_location,
            total_reqs,
        ],
    )
    t_collate.daemon = True
    t_collate.start()

    execute(clients, failures, duration)

    logging.debug("Waiting to join collate thread")
    t_collate.join()
