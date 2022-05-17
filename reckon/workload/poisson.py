import numpy as np
from typing import Iterator
from time import time
import reckon.reckon_types as t

class PoissonArrival(t.AbstractArrivalProcess):
    def __init__(
            self,
            rate : float,
            rand_seed : int =int(time())):
        self._rate = rate
        self._rng = np.random.default_rng(rand_seed)

    @property
    def arrival_times(self) -> Iterator[float]:
        # Poisson process => interarrival times are exponentially distributed with mean 1/rate
        # Thus we calculate period and then generate each arrival one at a time

        period = 1/self._rate
        curr = 0
        while True:
            yield curr
            curr += self._rng.exponential(period)
