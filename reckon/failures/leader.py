import reckon.reckon_types as t


class Fault(t.AbstractFault):
    def __init__(self, recovery, cluster, system, stoppers):
        self.r_rec = recovery
        self.cluster = cluster
        self.system = system
        self.stoppers = stoppers

    @property
    def id(self):
        return "Leader Fault"

    def apply_fault(self):
        leader = self.system.get_leader(self.cluster)
        self.stoppers[self.system.get_node_tag(leader)]()
        self.r_rec.killed = leader


class Recovery(t.AbstractFault):
    def __init__(self, system, restarters, killed=None):
        self.system = system
        self.restarters = restarters
        self.killed = killed

    @property
    def id(self):
        return "Recovery"

    def apply_fault(self):
        self.restarters[self.system.get_node_tag(self.killed)]()


class LeaderFailure(t.AbstractFailureGenerator):
    def get_failures(self, cluster, system, restarters, stoppers):
        r = Recovery(system, restarters)
        f = Fault(r, cluster, system, stoppers)
        return [t.NullFault(), f, r, t.NullFault()]
