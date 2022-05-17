import numpy as np
from time import time
import string
import itertools as it

from typing import List, Iterator, Union
import reckon.reckon_types as t

class UniformKeys(t.AbstractKeyGenerator):
    def __init__(
        self,
        write_ratio: float,
        max_key: int,
        payload_size: int,
        rand_seed=int(time()),
    ):
        self._write_ratio = write_ratio
        self._max_key = max_key
        self._payload_size = payload_size
        self._rng = np.random.default_rng(rand_seed)
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
    def prerequisites(self) -> List[t.Write]:
        return [
                t.Write(
                    kind=t.OperationKind.Write, key=self._new_key(k), value=""
                    )
                for k in range(self._max_key + 1)
                ]

    @property
    def workload(self) -> Iterator[Union[t.Read, t.Write]]:
        i = 0
        while True:
            yield (
                    t.Write(
                        kind=t.OperationKind.Write,
                        key=self._rand_key(),
                        value=self._uniform_payload(),
                        )
                    if self._should_gen_write_op() else 
                    t.Read(
                        kind=t.OperationKind.Read,
                        key=self._rand_key(),
                        )
            )
            i += 1

class UniformArrival(t.AbstractArrivalProcess):
    def __init__(self, rate):
        self._rate = rate

    @property
    def arrival_times(self) -> Iterator[float]:
        return it.count(0, 1/self._rate)

