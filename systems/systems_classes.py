import abc
from abc import abstractmethod

class AbstractSystem(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, args):
        self.log_location=args.system_logs
        self.client_class = self.get_client(args)
        self.client_type = args.client
        super(AbstractSystem, self).__init__()

    def __str__(self):
        return "{0}-{1}".format(self.system_type, self.client_type)

    def get_client_tag(host):
        return "mc_" + host.name

    def get_node_tag(host):
        return "node_" + host.name

    def start_screen(host, command):
        cmd = "screen -dmS {tag} bash -c \"{command}\"".format(tag=get_node_tag(host),command=command)
        host.cmdPrint(shlex.split(cmd))

    def kill_screen(host):
        host.cmd(shlex.split(("screen -X -S {0} quit").format(get_node_tag(host))))

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
    def cmd(ips, client_id, result_address):
        pass

