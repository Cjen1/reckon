from enum import Enum
from distutils.util import strtobool

from reckon.systems.etcd import Etcd, EtcdSBN, EtcdPreVote, EtcdPreVoteSBN
from reckon.systems.zookeeper import Zookeeper, ZookeeperFLE
from reckon.systems.ocons import OconsPaxos, OconsRaft, OconsRaftSBN, OconsRaftPrevote, OconsRaftPrevoteSBN
from reckon.systems.ocons import OConsConspireLeader, OConsConspireDC, OConsConspireLeaderDC
import reckon.reckon_types as t


class SystemType(Enum):
    Etcd = "etcd"
    EtcdPreVote = "etcd-pre-vote"
    EtcdSBN = "etcd+sbn"
    EtcdPreVoteSBN = "etcd-pre-vote+sbn"
    Zookeeper = "zookeeper"
    ZookeeperFLE = "zookeeper-fle"
    OconsPaxos = "ocons-paxos"
    OconsRaft = "ocons-raft"
    OconsRaftPrevote = "ocons-raft-pre-vote"
    OconsRaftSBN = "ocons-raft+sbn"
    OconsRaftPrevoteSBN = "ocons-raft-pre-vote+sbn"
    OConsConspireLeader = "ocons-conspire-leader"
    OConsConspireDC = "ocons-conspire-dc"
    OConsConspireLeaderDC = "ocons-conspire-leader-dc"

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
        help="Log location for the system and its clients.",
    )

    system_group.add_argument(
        "--data-dir",
        default="./data",
        help="Location of any data stores, should be empty at the start of each test.",
    )

    system_group.add_argument(
        "--new_client_per_request",
        default=False,
        help="Should a new client be created per request.",
        type=lambda x: bool(strtobool(x)),
    )

    system_group.add_argument(
        "--failure_timeout",
        default=1.0,
        help="Timeout until failure detector triggers an election",
        type = float,
    )

    system_group.add_argument(
        "--delay_interval",
        default=0.010,
        help="Delay before command applied, should be > latency",
        type = float,
    )

def get_system(args) -> t.AbstractSystem:
    res = None
    if args.system_type is SystemType.Etcd:
        res = Etcd(args)
    elif args.system_type is SystemType.EtcdPreVote:
        res = EtcdPreVote(args)
    elif args.system_type is SystemType.EtcdSBN:
        res = EtcdSBN(args)
    elif args.system_type is SystemType.EtcdPreVoteSBN:
        res = EtcdPreVoteSBN(args)
    elif args.system_type is SystemType.Zookeeper:
        res = Zookeeper(args)
    elif args.system_type is SystemType.ZookeeperFLE:
        res = ZookeeperFLE(args)
    elif args.system_type is SystemType.OconsPaxos:
        res = OconsPaxos(args)
    elif args.system_type is SystemType.OconsRaft:
        res = OconsRaft(args)
    elif args.system_type is SystemType.OconsRaftSBN:
        res = OconsRaftSBN(args)
    elif args.system_type is SystemType.OconsRaftPrevote:
        res = OconsRaftPrevote(args)
    elif args.system_type is SystemType.OconsRaftPrevoteSBN:
        res = OconsRaftPrevoteSBN(args)
    elif args.system_type is SystemType.OConsConspireLeader:
        res = OConsConspireLeader(args)
    elif args.system_type is SystemType.OConsConspireDC:
        res = OConsConspireDC(args)
    elif args.system_type is SystemType.OConsConspireLeaderDC:
        res = OConsConspireLeaderDC(args)
    else:
        raise Exception("Not supported system type: " + str(args.system_type))
    res.system_type = args.system_type
    return res
