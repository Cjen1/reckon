import shlex
import logging
import time
import os
from sys import stdout
import abc
from abc import abstractmethod


class AbstractSystem(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, args):
        ctime = time.localtime()
        creation_time = time.strftime("%H:%M:%S", ctime)

        self.system_type = args.system_type
        self.log_location = args.system_logs
        if not os.path.exists(args.system_logs):
            os.makedirs(args.system_logs)
        self.creation_time = creation_time
        self.client_class = self.get_client(args)
        self.client_type = args.client
        super(AbstractSystem, self).__init__()

    def __str__(self):
        return "{0}-{1}".format(self.system_type, self.client_type)

    def get_client_tag(self, host):
        return "mc_" + host.name

    def get_node_tag(self, host):
        return "node_" + host.name

    def start_screen(self, host, command):
        FNULL = open(os.devnull, "w")
        cmd = 'screen -dmS {tag} bash -c "{command}"'.format(
            tag=self.get_node_tag(host), command=command
        )
        logging.debug("Starting screen on {0} with cmd {1}".format(host.name, cmd))
        host.popen(shlex.split(cmd), stdout=FNULL, stderr=FNULL)

    def kill_screen(self, host):
        cmd = ("screen -X -S {0} quit").format(self.get_node_tag(host))
        logging.debug("Killing screen on host {0} with cmd {1}".format(host.name, cmd))
        host.cmd(shlex.split(cmd))

    def add_logging(self, cmd, tag):
        return cmd + " 2>&1 | tee -a {log}/{time_tag}_{tag}".format(
            log=self.log_location, tag=tag, time_tag=self.creation_time
        )

    @abstractmethod
    def get_client(self, args):
        pass

    @abstractmethod
    def start_nodes(self, cluster):
        pass

    @abstractmethod
    def start_client(self, client, client_id, cluster):
        pass

    @abstractmethod
    def get_leader(self, cluster):
        return None


class AbstractClient(object):
    __metaclass__ = abc.ABCMeta

    @abstractmethod
    def cmd(self, ips, client_id, result_address):
        pass
