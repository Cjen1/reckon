import logging
from threading import Thread
import time
import sys
import selectors

from typing import List
import itertools as it

import reckon.reckon_types as t

from tqdm import tqdm


def preload(ops_provider: t.AbstractWorkload, duration: float) -> int:
    logging.debug("PRELOAD: begin")

    

    for op, client in zip(ops_provider.prerequisites, it.cycle(ops_provider.clients)):
        client.send(t.preload(prereq=True, operation=op))

    sim_t = 0
    total_reqs = 0
    with tqdm(total=duration) as pbar:
        for client, op in ops_provider.workload:
            if op.time >= duration:
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

    for i, cli in enumerate(clients):
        cli.register_selector(sel, selectors.EVENT_READ, i)

    for _ in range(len(clients)):
        i = sel.select()[0][0].data

        msg = clients[i].recv()
        assert msg.__root__.kind == "ready"

    logging.debug("READY: end")


def execute(clients: List[t.Client], failures: List[t.AbstractFault], duration: float):
    logging.debug("EXECUTE: begin")

    if len(failures) <= 0:
        failures = [t.NullFault()]

    first_fault = failures[0]
    failures = failures[1:]

    first_fault.apply_fault()

    n_failures = len(failures)
    sleep_time = duration / (n_failures + 1)

    for client in clients:
        client.send(t.start())

    start_time = time.time()
    failure_times = [i * sleep_time + start_time for i, _ in enumerate(failures)]

    for i, (failure_time, failure) in enumerate(zip(failure_times, failures)):
        sleep_time: float = failure_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        logging.info(f"Executing failure #{i}:{failure.id}")
        failure.apply_fault()

    logging.debug("EXECUTE: end")


def collate(clients: List[t.Client], total_reqs: int) -> t.Results:
    logging.debug("COLLATE: begin")

    sel = selectors.DefaultSelector()

    for i, client in enumerate(clients):
        client.register_selector(sel, selectors.EVENT_READ, i)

    resps = []
    remaining_clients = len(clients)
    print(f"rem_cli: {remaining_clients}")
    with tqdm(total=total_reqs, desc="Results") as pbar:
        while remaining_clients > 0:
            i = sel.select()[0][0].data
            msg = clients[i].recv()
            if msg.__root__.kind == "finished":
                remaining_clients -= 1
                clients[i].unregister_selector(sel, selectors.EVENT_READ)
            elif msg.__root__.kind == "result":
                pbar.update(1)
                assert type(msg.__root__) is t.Result
                resps.append(msg.__root__)
            else:
                print(f"Unexpected message: |{msg}|")
    print("finished collate")
    return t.Results(__root__=resps)


def test_steps(
    clients: List[t.Client],
    workload: t.AbstractWorkload,
    failures: List[t.AbstractFault],
    duration: float,
) -> t.Results:

    workload.clients = clients
    total_reqs = preload(workload, duration)
    ready(clients)

    t_execute = Thread(
        target=execute,
        args=[clients, failures, duration],
    )
    t_execute.daemon = True
    t_execute.start()

    resps = collate(clients, total_reqs)

    t_execute.join()

    return resps


def run_test(
    test_results_location: str,
    mininet_clients: List[t.MininetHost],
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
        system.start_client(client, str(client_id), cluster)
        for client_id, client in enumerate(mininet_clients)
    ]
    logging.debug("Microclients started")

    resps = test_steps(clients, ops_provider, failures, duration)

    logging.debug(f"COLLATE: received, writing to {test_results_location}")
    with open(test_results_location, "w") as fres:
        fres.write(resps.json())
    logging.debug("COLLATE: end")
