from enum import Enum
from distutils.util import strtobool

from reckon.systems.etcd import Etcd, EtcdPreVote
import reckon.reckon_types as t

class SystemType(Enum):
    Etcd = "etcd"
    EtcdPreVote = "etcd-pre-vote"

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
        help='Should a new client be created per request',
        type=lambda x:bool(strtobool(x))
    )

def get_system(args) -> t.AbstractSystem:
    res = None
    if args.system_type is SystemType.Etcd:
        res = Etcd(args)
    elif args.system_type is SystemType.EtcdPreVote:
        res = EtcdPreVote(args)
    else:
        raise Exception("Not supported system type: " + args.system_type)
    res.system_type = args.system_type
    return res
