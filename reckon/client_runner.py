import logging
import threading
import time
import sys
import selectors
import itertools as it

from typing import List
import itertools as it

import reckon.reckon_types as t

from tqdm import tqdm

class MBox:
    def __init__(self, value=None):
        self.value = value
        self.mtx = threading.Lock()

    def __get__(self, instance, owner):
        with self.mtx:
            return self.value

    def __set__(self, instance, value):
        with self.mtx:
            self.value = value

class StallCheck:
    def __init__(self, init):
        self._value = init
        self.prev_read = self._value

        self.mtx = threading.Lock()

    def incr(self, delta = 1):
        with self.mtx:
            self._value += delta

    def check_if_stalled(self) -> bool:
        with self.mtx:
            current_val = self._value
            prev_val = self.prev_read

            self.prev_read = current_val

            return current_val == prev_val

class StalledException(Exception):
    pass

def terminate_if_stalled(task, timeout=30):
    stall_check = StallCheck(0)
    result = MBox()
    def wrapped_task(sc=stall_check, result=result):
        result.value = task(sc)

    thread = threading.Thread(target=wrapped_task, daemon=True)
    thread.start()

    ticker = 0

    while thread.is_alive():
        time.sleep(1.)
        if not stall_check.check_if_stalled():
            ticker = 0
            continue
        
        ticker += 1
        if ticker > timeout:
            raise StalledException

    thread.join(10)
    return result.value

def preload(stall_checker: StallCheck, ops_provider: t.AbstractWorkload, duration: float) -> int:
    logging.debug("PRELOAD: begin")

    for op, client in zip(ops_provider.prerequisites, it.cycle(ops_provider.clients)):
        client.send(t.preload(prereq=True, operation=op))

    sim_t = 0
    total_reqs = 0
    with tqdm(total=duration) as pbar:
        for client, op in ops_provider.workload:
            stall_checker.incr()
            if op.time >= duration:
                break

            total_reqs += 1
            client.send(t.preload(prereq=False, operation=op))

            pbar.update(op.time - sim_t)
            sim_t = op.time

    for client in ops_provider.clients:
        stall_checker.incr()
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

def sleep_til(x):
    diff = x - time.time() 
    if diff > 0:
        time.sleep(diff)

def roundrobin(*iterables):
    from itertools import cycle, islice
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    num_active = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while num_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            num_active -= 1
            nexts = cycle(islice(nexts, num_active))

def execute(clients: List[t.Client], failures: List[t.AbstractFault], duration: float):
    logging.debug("EXECUTE: begin")
    assert(len(failures) >= 2) # fence pole style, one at start, one at end, some in the middle

    sleep_dur = duration / (len(failures) - 1)

    start_time = time.time()

    fault_times = [start_time + i * sleep_dur for i, _ in enumerate(failures)]
    sleep_funcs = [lambda t=t: sleep_til(t) for t in fault_times][1:]
    fault_funcs = [lambda f=f: f.apply_fault() for f in failures]

    for client in clients:
        client.send(t.start())

    for f in roundrobin(fault_funcs, sleep_funcs): # alternate between sleeping and 
        f()

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

    assert(len(failures) >= 2)

    workload.clients = clients
    total_reqs = terminate_if_stalled(lambda stall_check: preload(stall_check, workload, duration))
    ready(clients)

    t_execute = threading.Thread(
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
