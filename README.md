# Concensus System Benchmark

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



