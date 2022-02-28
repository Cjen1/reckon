import logging
import time
import threading

import reckon.reckon_types as t

logging.basicConfig(
    format="%(asctime)s %(message)s", datefmt="%I:%M:%S %p", level=logging.DEBUG
)


class IntermittentPPartitionFailure(t.AbstractFailureGenerator):
    def __init__(self, sleep_duration):
        self.sleep_duration = sleep_duration
        self.partition = None
        self.cluster = None
        self.system = None
        self.partitioned = []
        self.failure_fixed = None

    def add_partition(self, host, remote):
        cmd = "iptables -I OUTPUT -d {0} -j DROP".format(remote.IP())
        logging.debug("cmd on {0} = {1}".format(host.name, cmd))
        host.cmd(cmd, shell=True)
        self.partitioned.append(host)

    def heal_partition(self):
        cmd = "iptables -D OUTPUT 1"
        for host in self.partitioned:
            host.cmd(cmd, shell=True)
            logging.debug("cmd on {0} = {1}".format(host.name, cmd))
        self.partitioned = []

    def initiate_failure(self):
        leader = self.system.get_leader(self.cluster)
        non_leader = [h for h in self.cluster if not h == leader][0]
        self.failure_fixed = threading.Event()
        def thread_fn(self=self, leader=leader, non_leader=non_leader):
            while not self.failure_fixed.isSet():
                print("Partitioning {0} {1}".format(leader.name, non_leader.name))
                self.add_partition(leader, non_leader)
                self.add_partition(non_leader, leader)
                time.sleep(self.sleep_duration)
                self.heal_partition()
                time.sleep(self.sleep_duration)

        thread = threading.Thread(
                target=thread_fn,
                args=[]
                )
        thread.start()

    def remove_failure(self):
        self.failure_fixed.set()

    def get_failures(self, cluster, system, restarters, stoppers):
        self.partitioned = []
        self.cluster = cluster
        self.system = system
        return [
            lambda self=self: self.initiate_failure(),
            lambda self=self: self.remove_failure(),
        ]
