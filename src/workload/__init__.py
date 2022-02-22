from enum import Enum
from src.workload.uniform import UniformOpsProvider

import reckon_types as t

# TODO abstract class for generators

class WorkloadType(Enum):
    Uniform = "uniform"

    def __str__(self):
        return self.value

def register_ops_args(parser):
    workload_group = parser.add_argument_group("workload")

    workload_group.add_argument(
        "workload_type", type=WorkloadType, choices=list(WorkloadType)
    )

    workload_group.add_argument(
        "--rate",
        type=float,
        default=100,
        help="rate of requests, defaults to %(default)s",
    )

    workload_group.add_argument(
        "--write-ratio",
        type=float,
        default=1,
        help="percentage of client's write operation, defaults to %(default)s",
    )

    workload_group.add_argument(
        "--max-key",
        type=int,
        default=1,
        help="maximum size of the integer key, defaults to %(default)s",
    )


    workload_group.add_argument(
        "--payload-size",
        type=int,
        default=10,
        help="upper bound of write operation's payload size in bytes, defaults to %(default)s",
    )

def get_ops_provider(args) -> t.AbstractWorkload:
    if args.workload_type is WorkloadType.Uniform:
        return UniformOpsProvider(
                rate=args.rate,
                write_ratio=args.write_ratio,
                max_key=args.max_key,
                payload_size=args.payload_size,
                clients=[],
            )
    else:
        raise Exception("Not supported workload type: " + args.workload_type)
