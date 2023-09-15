# Reckon - Benchmarking consensus systems for availability under failures.

As seen at [HAOC21: Examining Raft's behaviour during partial network failures](https://dl.acm.org/doi/10.1145/3447851.3458739).

## Installation

First openvswitch must be loaded as a kernel module on the host.
On ubuntu this is done by `apt install openvswitch-switch`, however other distributions will require an equivalent but different invocation.

### Recommended method with Docker

Run `make docker` to build a docker container containing all dependencies required to run a test with any of the clients, and to subsequently start it up, putting you into a Bash shell.

### Manual approach

- Install mininet
- Build the relevant system and client via `cd systems/<relevant-system> && make system && make client`

## Running a test
A typical test has the following steps:
- Build docker image and enter the container with `make` ~10 mins
- Define the desired test and run with `python -m reckon <other arguments>`

Positional arguments are as follows: `<system> <topology> <workload> <fault>`
  - Supported systems:
    - `etcd`: the strongly consistent key value store used in Kubernetes.
  - Supported topologies:
    - `simple`: A star topology with end-to-end loss and latency configurable via `--link-loss` and `--link-latency`.
    - `wan`: A WAN style network with `--number-nodes` data-centers with a node and a client in each data-center.
  - Supported workloads:
    - `uniform`: Keys are uniformly distributed in [0,`--max-key`], values are `--payload-size` bytes long strings.
  - Supported faults:
    - `none`: no fault occurs
    - `leader`: The leader is killed at 1/3 of the duration (T), and recovers at 2/3T.
    - `partial-partition`: A partial partition is injected at 1/3T and removed at 2/3T. This blocks communication between the leader of the cluster and one follower
    - `intermittent-partial`/`intermittent-full`: An intermittent full and partial partiion between one node (who is initially the leader) and a follower. The leader is always able to communicate with a majority of nodes. Time between faults is set by `--mtbf`.
    - `kill-n`: kill `--kill-n` at the start of the test. This tests maximal fault situations when some of the cluster has died at the start of the test. 
  - Other arguments
    - `-d`: enter a debug mininet cli where the topology is constructed and system started.
    - `--duration`: duration of the test.
    - `--result-location`: where to write the results of the test.

This can be automated as in `scripts/tester.py` or `scripts/lossy_etcd.py`, and a safer running environment is `scripts/run.sh <command>`.
