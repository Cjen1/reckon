# Reckon - Benchmarking consensus systems for availability under failures.

## Installation

### Recommended method with Docker

Run `make docker` to build a docker container containing all dependencies required to run a test with any of the clients, and to subsequently start it up, putting you into a Bash shell.

### Manual approach

- Install mininet
- Build the relevant system and client via `cd systems/<relevant-system> && make system && make client`

## Running a test
A typical test would involve loading into the docker container with `make docker` before running at test with for example: `python benchmark.py etcd --client go simple uniform none`

The semantics of the command line arguments are discussed on the [wiki](https://github.com/Cjen1/reckon/wiki/Command-line-interface).
