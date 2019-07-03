# Template of a benchmark target

General Overview:
	- clients: all benchmarkable clients of the system (eg. go bindings for etcd, c bindings for etcd and python bindings for etcd
		- client contains all code required to produce a client executable called client in the named client folder.
	- scripts: scripts to start, stop, setup etc. fill in each script as appropiate
	- service: all things required to run the service, i.e. docker images etc

# ESTABLISHING A COMPARISON BETWEEN DIFFERENT CONSENSUS SYSTEMS
-- ZOOKEEPER

	0.1 - Problem Statement.
		There are various systems for achieving consensus, our goal is to establish a comparison
		between the most important ones based off testing under consistent conditions.
		This document outlines the setup for testing Apache Zookeeper and the procedures used.

	1.1 - Environment Setup.
		The Zookeeper tests were executed using replicated Zookeeper on three servers, each run-
		ning Ubuntu 16.0.4, with a fourth machine with identical hardware running the client(s)
		for each of the tests. The Zookeeper servers were situated in isolated Docker containers
		with the necessary ports exposed, with the Client being operated through Java using the
		official Zookeeper Java API. The tests were run through a Python script with the opera-
		tions being transmitted to the client via ZeroMQ. 

	1.2 - Zookeeper Deployment Details.
		- Zookeeper Release: 3.4.12
		- Replicated Mode (3/5 server setups.)
		- Configurations set: (all other configurations were left to default.)
		--- Tick Time = 2000ms
		--- Init Limit = 5 ticks
		--- Sync Limit = 2 ticks

	2.1 - Deployment Method.
		As the deployment of the official Zookeeper Docker image in replicated mode proved prob-
		lematic, which is partly a result of Docker Swarm using etcd, another of the consensus
		systems under our scrutiny, a custom Docker image was built, for which the Dockerfile 
		stepped through essentially the same process as installing Zookeeper without Docker, 
		with ready made config files for each of the servers being injected into the Docker 
		image at build. Here, the ports used for client interactions, normal quorum communica-
		tions, and leader elections were all exposed to the other servers.

	2.2 - Client Interfacing.
		A ZeroMQ Java client was written to receive the operations which were to be carried out,
		encoded using Google Protocol Buffers. These were then decoded, interpreted, and the 
		correct actions were carried out by an org.apache.zookeeper.ZooKeeper object. Time mea-
		surements were of course only started once the Operation had been successfully decoded
		and interpreted, and stopped once the operation had been carried out. The response times
 		and eventual error / exception messages were recorded and then sent as responses to the 
		received Operations. 

	3.1 - Testing Execution.
		To set up the Zookeeper System as in our experiment, use the Dockerfile as provided, the
		scripts as in ./scripts, and the configuratoins as in ./zkconfs, and execute the follow-
		ing steps.
		  1) Modify the zoo?.cfg files to fit your IP-addresses.
		  2) Distribute all of these files onto all of your servers.
		  3) Build, on all servers, the Docker image as based off the Dockerfile, giving the 
		     build command on each server the argument ZOO_MY_ID as consistent with your config 
		     files. Tag your image with a sensible name; here zkstart was used (zkstart5 for 5 
		     server setup.)
		  4) Repeat the above steps for the files in ./5ser to obtain the image for the five ser-
		     ver setup.
		  5) To execute the tests, switch into ./tester, and execute run_tests.py.
		     Note: Python 3.x will encounter issues with parsing, hence Python 2 is used here. 
		  6) The test suite is configurable by adding/altering tests of the form as advised in 
		     run_tests.py within the array of tests. To add new failure modes, or Operation sets, 
		     modify the files in ./tester/util.

