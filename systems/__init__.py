from enum import Enum

from systems.etcd import Etcd, EtcdPreVote
from systems.ocons import OConsPaxos

from distutils.util import strtobool


class SystemType(Enum):
    Etcd = "etcd"
    EtcdPreVote = "etcd-pre-vote"
    OConsPaxos = "ocons-paxos"

    def __str__(self):
        return self.value


def register_system_args(parser):
    system_group = parser.add_argument_group("system")

    system_group.add_argument("system_type", type=SystemType, choices=list(SystemType))

    # Can't inject a reasonable set of choices without knowing the system type unfortunately
    system_group.add_argument("--client")

    system_group.add_argument(
        "--system_logs",
        default="./logs",
        help="Log location for the system and its clients",
    )

    system_group.add_argument(
        "--new_client_per_request",
        default=False,
        help="Should a new client be created per request",
        type=lambda x: bool(strtobool(x)),
    )


def get_system(args):
    res = None
    if args.system_type is SystemType.Etcd:
        res = Etcd(args)
    elif args.system_type is SystemType.EtcdPreVote:
        res = EtcdPreVote(args)
    elif args.system_type is SystemType.OConsPaxos:
        res = OConsPaxos(args)
    else:
        raise Exception("Not supported system type: " + args.system_type)
    res.system_type = args.system_type
    return res
