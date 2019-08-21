# Concensus System Benchmark

## Installation

Prerequisites: Install containernet (easiest approach is to run the nested dockercontainer)

## Running a test

Run benchmark.py

Parameters are as follows:

System: The system to test, for example 'etcd_go' for etcd with a client using the go bindings

Topology: The topology to use for the testing, for example an edge network or just a simple fully connected data-center

	- --topo_args. Arguments to pass to the topology class, for example number of nodes, or clients

Distribution: The distribution of operations to pass, currently only a particular ratio of read or write operations which are uniformly distributed accross the keys.
	- --dist_args: Arguments to pass to the distribution, i.e. the ratio, key range or payload size

Failure type: The type of failure which will be injected, currently only leader failure or no failure, but should support network partitions etc

	- --fail_args: arguments for the failure, for example multiple consecutive leader failures etc

--benchmark_config: configuration of the benchmark for example rate or duration

-d : Debug flag to pause the test after startup and present the Mininet (Containernet) CLI for debug purposes

absolute_path: The absolute path in the host to this folder. This is the path to this folder in the host if operating in a nested docker environment with this folder being mounted into it.

A typical command to start a test would thus be:
```
python benchmark.py etcd_go simple --topo_args n=5,nc=2 uniform leader --benchmark_config rate=10,duration=15 /home/cjen1/resolving-consensus
```


## Setting up a new service 

### Prerequisites

	- A python script to set up the service on a given cluster of hosts, passing the hostnames of the endpoints as a comma separated list (no spaces)
	- A bash script to start the service on a given host, having argument <endpoint ip>
	- A bash script to stop the service on a given host, having argument <endpoint ip>

### Method

	copy each of the scripts into the scripts folder under the names: <service>_setup.sh <service>_start.sh <service>_stop.sh respectively
	
	edit the Makefile to build your client/s and copy them into the client folder (see names below) 

## Notes on file names of Custom Clients

The name of the system to set up is the prefix of the client name:
	<system>_<info about client>

eg

	etcd_go-basic

This allows easy picking up of the correct system to use for a given client without maintianing an explicit database (with lots of replication)

## Notes on names of Docker containers for distributed systems

make the name of the container the name of the service: (similarly to the client)

eg

	for zookeeper: name=zookeeper

	for ectd: name=etcd


## Notes on adding tests

Format of a test is (\<tag\>,\<hostname list\>,\<number of clients\>,\<operations\>,\<failure mode\>)
	
    - tag = the name of the test eg sequential-1S-1C-4K for a 1 server, 1 client sequential test with 4KB keys
	- hostsname list = a python list of host names
	- operations = a list of utils.op_gen.Op. Generate with a function in op_gen
	- failure mode = the failure that is injected: eg crashing clients

## Notes on adding failure tests

Format is a function which when given a service name will return two functions, (start failure, stop failure)



