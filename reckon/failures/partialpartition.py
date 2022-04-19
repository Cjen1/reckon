import logging
import reckon.reckon_types as t
from typing import Union
from typing_extensions import Literal


class Shared:
    def __init__(self, partitioned=[]):
        self._partitioned = partitioned

    @property
    def partitioned(self):
        return self._partitioned

    @partitioned.setter
    def partitioned(self, value):
        self._partitioned = value


class PartitionFault(t.AbstractFault):
    def __init__(
        self,
        kind: Union[Literal["create"], Literal["remove"]],
        shared: Shared,
        system,
        cluster,
    ):
        self._kind = kind
        self._shared = shared
        self.system = system
        self.cluster = cluster

    def initiate_partition(self):
        leader = self.system.get_leader(self.cluster)
        non_leader = [h for h in self.cluster if not h == leader][0]
        logging.debug("Partitioning %s from %s", leader.name, non_leader.name)
        self.partition(leader, non_leader)
        self.partition(non_leader, leader)

    def partition(self, host, remote):
        cmd = "iptables -I OUTPUT -d {0} -j DROP".format(remote.IP())
        logging.debug("cmd on {0} = {1}".format(host.name, cmd))
        host.cmd(cmd, shell=True)
        self._shared.partitioned.append(host)

    def remove_partition(self):
        cmd = "iptables -D OUTPUT 1"
        for host in self._shared.partitioned:
            host.cmd(cmd, shell=True)
            logging.debug("cmd on {0} = {1}".format(host.name, cmd))
        self._shared.partitioned = []

    def apply_fault(self):
        if self._kind == "create":
            self.initiate_partition()
        elif self._kind == "remove":
            self.remove_partition()


class PPartitionFailure(t.AbstractFailureGenerator):
    def get_failures(self, cluster, system, restarters, stoppers):
        shared = Shared()
        return [
            PartitionFault("create", shared, system, cluster),
            PartitionFault("remove", shared, system, cluster),
        ]
