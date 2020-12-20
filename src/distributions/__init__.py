from enum import Enum
from src.distributions.uniform import UniformOpsProvider


class DistributionType(Enum):
    Uniform = "uniform"

    def __str__(self):
        return self.value


def _parse_key_range_arg(key_range_raw):
    krl, kru = key_range_raw.split(">")
    return int(krl), int(kru)


def register_ops_args(parser):
    dist_group = parser.add_argument_group("distribution")

    dist_group.add_argument(
        "dist_type", type=DistributionType, choices=list(DistributionType)
    )

    dist_group.add_argument(
        "--write-ratio",
        type=float,
        default=0.5,
        help="percentage of client's write operation, defaults to %(default)s",
    )

    dist_group.add_argument(
        "--payload-size",
        type=int,
        default=10,
        help="upper bound of write operation's payload size in bytes, defaults to %(default)s",
    )

    dist_group.add_argument(
        "--key-range",
        type=_parse_key_range_arg,
        default="1>10",
        help="'>' separated lower and (inclusive) upper bound of keys, defaults to %(default)s",
    )


def get_ops_provider(args):
    if args.dist_type is DistributionType.Uniform:
        return UniformOpsProvider(
            key_range_lower=args.key_range[0],
            key_range_upper=args.key_range[1],
            payload_size=args.payload_size,
            write_ratio=args.write_ratio,
        )
    else:
        raise Exception("Not supported distribution type: " + args.dist_type)
