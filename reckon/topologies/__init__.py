from enum import Enum
from reckon.topologies.simple import SimpleTopologyProvider
from reckon.topologies.wan import WanTopologyProvider

import reckon.reckon_types as t


class TopologyType(Enum):
    Simple = "simple"
    Wan = "wan"

    def __str__(self):
        return self.value


def register_topo_args(parser):
    topo_group = parser.add_argument_group("topologies")

    topo_group.add_argument("topo_type", type=TopologyType, choices=list(TopologyType))

    topo_group.add_argument(
        "--number-nodes",
        type=int,
        default=3,
    )

    topo_group.add_argument(
        "--number-clients",
        type=int,
        default=1,
    )

    topo_group.add_argument(
        "--link-loss",
        type=float,
        default=0,
    )

    topo_group.add_argument("--link-latency", default="20ms")


def get_topology_provider(args) -> t.AbstractTopologyGenerator:
    if args.topo_type is TopologyType.Simple:
        return SimpleTopologyProvider(
            args.number_nodes, args.number_clients, args.link_latency, args.link_loss
        )
    elif args.topo_type is TopologyType.Wan:
        return WanTopologyProvider(
            args.number_nodes,
            args.link_latency,
        )
    else:
        raise Exception("Not supported distribution type: " + str(args.topo_type))
