import reckon.reckon_types as t
from typing import List, Dict, Any, Callable


class Fault(t.AbstractFault):
    def __init__(self, n, cluster, stoppers, system):
        self.n = n
        self.cluster = cluster
        self.stoppers = stoppers
        self.system = system

    def apply_fault(self):
        for i in range(self.n):
            self.stoppers[self.system.get_node_tag(self.cluster[i])]()


class KillN(t.AbstractFailureGenerator):
    def __init__(self, n):
        self.n = n

    def get_failures(
        self,
        cluster: List[t.MininetHost],
        system: t.AbstractSystem,
        _: Dict[Any, Callable[[], None]],
        stoppers: Dict[Any, Callable[[], None]],
    ) -> List[t.AbstractFault]:
        fault = Fault(self.n, cluster, stoppers, system)
        return [fault]
