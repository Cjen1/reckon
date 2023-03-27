import reckon.reckon_types as t


class Fault(t.AbstractFault):
    def __init__(self, cluster, system, stoppers):
        self.cluster = cluster
        self.system = system
        self.stoppers = stoppers

    @property
    def id(self):
        return "Leader Fault"

    def apply_fault(self):
        leader = self.system.get_leader(self.cluster)
        print(f"Killing {self.system.get_node_tag(leader)}")
        self.stoppers[self.system.get_node_tag(leader)]()


class LeaderOnlyFailure(t.AbstractFailureGenerator):
    def get_failures(self, cluster, system, restarters, stoppers):
        f = Fault(cluster, system, stoppers)
        return [t.NullFault(), f, t.NullFault()]
