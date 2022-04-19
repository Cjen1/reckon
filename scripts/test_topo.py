import argparse

from reckon.topologies import register_topo_args, get_topology_provider

parser = argparse.ArgumentParser(
        description="Sets up the topology and runs a series of tests"
    )

register_topo_args(parser)

arg_group = parser.add_argument_group("test")
arg_group.add_argument("-d", action="store_true",help="Open mininet CLI")

args = parser.parse_args()

if args.d:
    from mininet.cli import CLI

    net, _, _ = get_topology_provider(args).setup()

    CLI(net)

else:
    net, _, _ = get_topology_provider(args).setup()

    # TODO

