from enum import Enum
from abc import ABC, abstractmethod

from systems.etcd import Etcd

class AbstractSystem(ABC):
    def __init__(self, log_location, clientType):
        self.log_location=log_location
        self.clientClass = self.get_client(clientType)
        super().__init__()

    def start_screen(host, command, screen_name):
        cmd = "screen -dmS {tag} bash -c \"{command}\"".format(tag=tag,command=cmd)
        host.cmdPrint(shlex.split(cmd))

    def get_client_tag(host):
        return "mc_" + host.name

    def get_node_tag(host):
        return "etcd_" + host.name

    @abstractmethod
    def start_nodes(self, cluster):
        pass

    @abstractmethod
    def start_clients(self, cluster, clients):
        pass

    @abstractmethod
    def get_client(self, args):
        pass

    def get_leader(self, cluster):
        return None

class AbstractClient(ABC):
    @abstractmethod
    def cmd(ips, client_id, result_address):
        pass

class SystemType(Enum):
    Etcd = 'etcd'

    def __str__(self):
        return self.value


def register_system_args(parser):
    system_group = parser.add_argument_group('system')

    dist_group.add_argument(
        'system_type', type=SystemType,
        choices=list(SystemType))

    # Can't inject a reasonable set of choices without knowing the system type unfortunately
    dist_group.add_argument('--client')

def get_system(args):
    if args.system_type is SystemType.Etcd:
        return Etcd()
    else:
        raise Exception(
            'Not supported system type: ' + args.system_type
        )
