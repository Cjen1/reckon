from enum import Enum
from src.failures.leader import LeaderFailure
from src.failures.none import NoFailure
from src.failures.partialpartition import PPartitionFailure
from src.failures.intermittent import IntermittentPPartitionFailure


class FailureType(Enum):
    FNone = "none"
    FLeader = "leader"
    FPartialPartition = "partial-partition"
    FIntermittentPP = "intermittent"

    def __str__(self):
        return self.value

def register_failure_args(parser):
    dist_group = parser.add_argument_group("failures")

    dist_group.add_argument("failure_type", type=FailureType, choices=list(FailureType))

    dist_group.add_argument("--mtbf", type=float, default=0.1)


def get_failure_provider(args):
    if args.failure_type is FailureType.FNone:
        return NoFailure()
    elif args.failure_type is FailureType.FLeader:
        return LeaderFailure()
    elif args.failure_type is FailureType.FPartialPartition:
        return PPartitionFailure()
    elif args.failure_type is FailureType.FIntermittentPP:
        return IntermittentPPartitionFailure(args.mtbf)
    else:
        raise Exception("Not supported failure type: " + args.dist_type)
