import numpy as np
from time import time
import string

from typing import List
import reckon.reckon_types as t


class UniformOpsProvider(t.AbstractWorkload):
    def __init__(
        self,
        rate: float,
        write_ratio: float,
        max_key: int,
        payload_size: int,
        clients: List[t.Client],
        rand_seed=int(time()),
    ):
        self._rate = rate
        self._write_ratio = write_ratio
        self._max_key = max_key
        self._payload_size = payload_size
        self._rng = np.random.default_rng(rand_seed)
        self._clients = clients
        self.ALPHABET = np.array(list(string.ascii_lowercase))

    # TODO test that _new_key generates correct length keys
    def _new_key(self, i):
        max_key_digits = len(str(self._max_key))
        return str(i).zfill(max_key_digits)

    def _rand_key(self):
        return self._new_key(self._rng.integers(0, self._max_key + 1))

    def _uniform_payload(self):
        return "".join(
            self._rng.choice(self.ALPHABET, size=self._payload_size).tolist()
        )

    def _should_gen_write_op(self):
        return self._rng.random() < self._write_ratio

    @property
    def clients(self):
        return self._clients

    @clients.setter
    def clients(self, value):
        self._clients = value

    @property
    def prerequisites(self) -> List[t.WorkloadOperation]:
        return [
            (
                self._clients[0],
                t.Operation(
                    payload=t.Write(
                        kind=t.OperationKind.Write, key=self._new_key(k), value=""
                    ),
                    time=0,
                ),
            )
            for k in range(self._max_key + 1)
        ]

    @property
    def workload(self):
        i = 0
        period = 1 / self._rate
        while True:
            yield (
                self._clients[i % len(self._clients)],
                (
                    t.Operation(
                        time=i * period,
                        payload=t.Write(
                            kind=t.OperationKind.Write,
                            key=self._rand_key(),
                            value=self._uniform_payload(),
                        ),
                    )
                    if self._should_gen_write_op()
                    else t.Operation(
                        time=i * period,
                        payload=t.Read(
                            kind=t.OperationKind.Read,
                            key=self._rand_key(),
                        ),
                    )
                ),
            )
            i += 1
