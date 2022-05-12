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
        stats = "\n".join(
                f"{host.name}:\n{self.system.stat(host)}"
                for host in self.cluster
                )
        print(stats)

class StatFault(t.AbstractFailureGenerator):
    def get_failures(self, cluster, system, restarters, stoppers):
        f = Fault(cluster, system, stoppers)
        return [t.NullFault(), f, f]
