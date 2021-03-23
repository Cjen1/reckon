# Consensus System Benchmark

## Installation

### Recommended method with Docker

Run `make docker` to build a docker container containing all dependencies required to run a test with any of the clients, and to subsequently start it up, putting you into a Bash shell.

### Other methods

- Install mininet
- Build the relevant system and client via `cd systems/<relevant-system> && make system && make client`

## Running a test

`python benchmark.py <system> <topology> <distribution> <failure>`

### Parameters

#### `<system>` = `etcd`, `etcd-pre-vote`
The system to test for example `etcd`

`--client`: The relevant system's client.

`--system_logs`: The log location for the system and its clients.

`--new_client_per_request`: Whether to use a new client per request or to reuse the same client. This is False by default.

#### `<topology>` = `simple`, `wan`
The mininet topology to use.

`--number-nodes`: The number of nodes in the system.

`--number-clients`: the number of clients.

`--link-latency`: The latency of the links between nodes. In the WAN topology this is the latency to a central switch, so the end to end latency is twice this.

#### `<distribution>` = `uniform`
The distribution of keys in the requests.

`--write-ratio`: What fraction of the requests are write requests

`--payload-size`: How large write requests payload are in bytes

`--key-range`: The range of keys, '>' separated lower and (inclusive) upper bound of integer keys.

#### `<failure>` = `none`, `leader`, `partial-partition`, `intermittent-partial`, `intermittent-full`
The failure to apply to the system.
This returns some number of pertubations to inject into the system which are then applied at even intervals throughout the test.

For example `none` means no failures are injected, while `leader` injects two pertubations, one to kill the leader, one to bring it back up. This means that in the `leader` failure case on a 60s test, it will have 20s before the leader is killed, 20s of the leader being dead and 20s after it recovers.

`intermittent-<partition-type>`: These failures transition between the underlying failure being in place or removed at relatively high frequency. The frequency of transitions is governed by `--mtbf` where there is that length in seconds between each transition.


### Running a test
A typical test would involve loading into the docker container with `make docker` before running at test with `python benchmark.py etcd --client go simple uniform none`
