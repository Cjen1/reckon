import logging
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%I:%M:%S %p', level=logging.DEBUG)

class PPartitionFailure():
    def partition(self, host, remote):
        cmd = "iptables -I OUTPUT -d {0} -j DROP".format(remote.IP())
        host.cmd(cmd, shell=True)
        self.partitioned.append(host)

    def initiate_partition(self):
        leader = self.system.get_leader(self.cluster)
        non_leader = [h for h in self.cluster if not h == leader][0]
        logging.debug("Partitioning %s from %s", leader.name, non_leader.name)
        self.partition(leader, non_leader)
        self.partition(non_leader, leader)

    def remove_partition(self):
        cmd = "iptables -D OUTPUT 1"
        for host in self.partitioned:
            host.cmd(cmd, shell=True)
        self.partitioned = []

    def get_failures(self, cluster, system, restarters, stoppers):
        self.partitioned = []
        self.cluster = cluster
        self.system = system
        return [
                lambda self=self: self.initiate_partition(),
                lambda self=self: self.remove_partition()
                ]
