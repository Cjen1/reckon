import numpy.random as rand
from src.utils.req_factory import ReqFactory
from time import time


class UniformOpsProvider(object):
    def __init__(
        self,
        key_range_lower=1,
        key_range_upper=10,
        payload_size=10,
        write_ratio=0.5,
        rand_seed=int(time())
    ):
        self._key_range_lower = key_range_lower
        self._key_range_upper = key_range_upper
        self._payload_size = payload_size
        self._write_ratio = write_ratio
        rand.seed(rand_seed)

    def _rand_key(self):
        return rand.random_integers(
            self._key_range_lower,
            self._key_range_upper
        )

    def _uniform_payload(self):
        return rand.bytes(self._payload_size)

    def _should_gen_write_op(self):
        return rand.ranf() < self._write_ratio

    @property
    def prereqs(self):
        return [
            ReqFactory.write(k, b'0', 0, prereq=True)
            for k in range(self._key_range_lower, self._key_range_upper + 1)
        ]

    def get_ops(self, start):
        if self._should_gen_write_op():
            return ReqFactory.write(
                self._rand_key(),
                self._uniform_payload(),
                start
            )
        else:
            return ReqFactory.read(self._rand_key(), start)
