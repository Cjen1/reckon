from enum import Enum

from systems.etcd import Etcd, EtcdNoCheckQuorum, EtcdDebug


class SystemType(Enum):
    Etcd = "etcd"

    EtcdNoCheckQuorum = "etcdNoCQ"

    EtcdDebug = "etcdDebug"

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


def get_system(args):
    res = None
    if args.system_type is SystemType.Etcd:
        res = Etcd(args)
    elif args.system_type is SystemType.EtcdNoCheckQuorum:
        res = EtcdNoCheckQuorum(args)
    elif args.system_type is SystemType.EtcdDebug:
        res = EtcdDebug(args)
    else:
        raise Exception("Not supported system type: " + args.system_type)
    res.system_type = args.system_type
    return res
