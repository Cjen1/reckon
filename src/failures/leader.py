class LeaderFailure:
    def leader_down(self):
        leader = self.system.get_leader(self.cluster)
        self.stoppers[self.system.get_node_tag(leader)]()
        self.killed = leader

    def leader_recovery(self):
        leader = self.killed
        self.restarters[self.system.get_node_tag(leader)]()

    def get_failures(self, cluster, system, restarters, stoppers):
        self.cluster = cluster
        self.system = system
        self.restarters = restarters
        self.stoppers = stoppers
        return [
            lambda self=self: self.leader_down(),
            lambda self=self: self.leader_recovery(),
        ]
