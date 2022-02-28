import numpy as np
from time import time

from typing import List, Iterator
from reckon.reckon_types import Client, WorkloadOperation, AbstractWorkload, Read, Write, Operation, OperationKind

class UniformOpsProvider(AbstractWorkload):
    def __init__(
        self,
        rate: float,
        write_ratio: float,
        max_key: int,
        payload_size: int,
        clients: List[Client],
        rand_seed=int(time()),
    ):
        self._rate = rate
        self._write_ratio = write_ratio
        self._max_key = max_key
        self._payload_size = payload_size
        self._rng = np.random.default_rng(rand_seed)
        self._clients = clients

    #TODO test that _new_key generates correct length keys
    def _new_key(self, i):
        max_key_digits = len(str(self._max_key))
        return str(i).zfill(max_key_digits)

    def _rand_key(self):
        return self._new_key(self._rng.integer(0, self._max_key + 1))

    def _uniform_payload(self):
        return self._rng.bytes(self._payload_size)

    def _should_gen_write_op(self):
        return self._rng.random() < self._write_ratio

    @property
    def clients(self):
        return self._clients

    @clients.setter
    def clients(self, value):
        self._clients = value

    @property
    def prerequisites(self) -> List[WorkloadOperation]:
        return [
                (self._clients[0], Operation(
                    payload = Write(
                        kind= OperationKind.Write,
                        key=self._new_key(k),
                        value = ""), 
                    time = 0))
                for k in range(self._max_key + 1)
                ]

    def workload(self, start) -> Iterator[WorkloadOperation]:
        time = start
        i = 0
        period = 1 / self._rate
        while True:
            if self._should_gen_write_op():
                yield (self._clients[i % len(self._clients)], 
                        Operation(
                            payload = Write(
                                kind= OperationKind.Write,
                                key= self._rand_key(),
                                value= self._uniform_payload()),
                            time= time))
            else:
                yield (self._clients[i % len(self._clients)], 
                        Operation(
                            payload= Read(
                                kind = OperationKind.Read,
                                key= self._rand_key()),
                            time=time,
                            ))

            time += period
            i += 1
