from enum import Enum
from src.failures.leader import LeaderFailure
from src.failures.none import NoFailure
from src.failures.partialpartition import PPartitionFailure


class FailureType(Enum):
    FNone = "none"
    FLeader = "leader"
    FPartialPartition = "partial-partition"

    def __str__(self):
        return self.value


def register_failure_args(parser):
    dist_group = parser.add_argument_group("failures")

    dist_group.add_argument("failure_type", type=FailureType, choices=list(FailureType))


def get_failure_provider(args):
    if args.failure_type is FailureType.FNone:
        return NoFailure()
    elif args.failure_type is FailureType.FLeader:
        return LeaderFailure()
    elif args.failure_type is FailureType.FPartialPartition:
        return PPartitionFailure()
    else:
        raise Exception("Not supported failure type: " + args.dist_type)
