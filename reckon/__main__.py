import argparse

from reckon.client_runner import run_test
from reckon.workload   import register_ops_args,     get_ops_provider
from reckon.failures   import register_failure_args, get_failure_provider
from reckon.topologies import register_topo_args,    get_topology_provider
from reckon.systems    import register_system_args,  get_system

import logging

logging.basicConfig(
  format="%(asctime)s %(message)s", datefmt="%I:%M:%S %p", level=logging.DEBUG
)


if __name__ == "__main__":
    # ------- Parse arguments --------------------------
    parser = argparse.ArgumentParser(
        description="Runs a benchmark of a local fault tolerant datastore"
    )

    register_system_args(parser)
    register_topo_args(parser)
    register_ops_args(parser)
    register_failure_args(parser)

    arg_group = parser.add_argument_group("benchmark")
    arg_group.add_argument("-d", action="store_true", help="Debug mode")
    arg_group.add_argument("--duration", type=float, default=60)
    arg_group.add_argument("--result-location", default="test.res")

    args = parser.parse_args()

    print(f"Args = {args}")

    if args.d:
        from mininet.cli import CLI

        system = get_system(args)
        topo_provider = get_topology_provider(args)
        failure_provider = get_failure_provider(args)
        ops_provider = get_ops_provider(args)

        net, cluster, _ = topo_provider.setup()

        _, stoppers = system.start_nodes(cluster)

        CLI(net)

        for stopper in stoppers.values():
            stopper()
    else:
        stoppers = {}
        try:
          system = get_system(args)
          topo_provider = get_topology_provider(args)
          failure_provider = get_failure_provider(args)
          ops_provider = get_ops_provider(args)

          net, cluster, clients = get_topology_provider(args).setup()

          restarters, stoppers_prime = system.start_nodes(cluster)
          stoppers = stoppers_prime

          failures = failure_provider.get_failures(cluster, system, restarters, stoppers)

          print("BENCHMARK: testing connectivity, and allowing network to settle")
          net.pingAll()

          print("BENCHMARK: Starting Test")

          run_test(
              args.result_location,
              clients,
              ops_provider,
              args.duration,
              system,
              cluster,
              failures,
          )
        finally:
          for stopper in stoppers.values():
              stopper()
          logging.info("Finished Test")
