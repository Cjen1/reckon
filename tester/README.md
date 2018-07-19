# Concensus System Benchmark

## Notes on file names of Language Specific Clients

The name of the system to set up is the prefix of the client name:
	<system>_<info about client>

eg
	etcd_go-basic

This allows easy picking up of the correct system to use for a given client without maintianing an explicit database (with lots of replication)

## Notes on names of Docker containers for distributed systems

make the name of the container the name of the service: (similarly to the client)
eg
	for ectd, name=etcd
	for zookeeper, name=zookeeper


