class LeaderFailure():
    def leader_down(self):
        leader = self.system.get_leader(self.net)
        self.stoppers[self.system.get_node_tag(leader)]()
        self.killed = leader

    def leader_recovery(self):
        leader = self.killed
        self.restarters[self.system.get_node_tag(leader)]()

    def get_failures(self, net, system, restarters, stoppers):
        self.net = net
        self.system = system
        self.restarters = restarters
        self.stoppers = stoppers
        return [
                lambda self=self: self.leader_down()
                lambda self=self: self.leader_recovery()
                ]
