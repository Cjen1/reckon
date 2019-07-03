# Template of a benchmark target

General Overview:
	- clients: all benchmarkable clients of the system (eg. go bindings for etcd, c bindings for etcd and python bindings for etcd
		- client contains all code required to produce a client executable called client in the named client folder.
	- scripts: scripts to start, stop, setup etc. fill in each script as appropiate
	- service: all things required to run the service, i.e. docker images etc
