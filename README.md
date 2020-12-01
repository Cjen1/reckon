# Consensus System Benchmark

This tool aims to leverage mininet to allow more comprehesive testing of distributed databases.

It places in an emulated network some number of nodes running the system (emulating racks in a datacenter) and a client spawner (representing the gateway through which clients would contact the system).

Currently supported features:

- Arbitrary tree network topologies
- Arbitrary node/network failures
- Arbitrary workloads

Currently implemented features:

- Datacenter style networks
- Leader and follower node failures/recoveries
- Uniformly distributed read/write requests

Current limitations:

- No loops in topologies

## Installation

1. Install Docker
2. Clone this repository
3. `make docker`

## Running a test

Running `scripts/run.sh` after `make docker` will run a series of tests. 

## Setting up a new service 

Inside a folder `<system>` in systems place the following artifacts:

- `systems/<system>/scripts/setup.py` : A python script to set up the service on a given cluster of hosts, passing the hostnames of the endpoints as a comma separated list (no spaces).
- `systems/<system>/scripts/client-start.py` A python script to set up a client on a given mininet host.
- `systems/<system>/clients/<tag>/client` A client shim which will apply requests to the system (libraries exist for `go` and `ocaml`).

If you want to support leader failures then `systems/<system>/scripts/find-leader.py` is necessary to determine which node is the leader.

In all of these cases a good maintained example is `systems/etcd`.
