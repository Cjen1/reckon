#!/usr/bin/env bash

set -x

service openvswitch-switch start
ovs-vsctl set-manager ptcp:6640

timeout 30 \
	python benchmark.py etcd --client go --system_logs ./logs \
	simple --topo_args n=1,nc=1 uniform --write-ratio 1 none \
	--benchmark_config rate=1000,duration=10

EXITCODE=$?

service openvswitch-switch stop

if [ $EXITCODE -eq 0 ]
then 
	exit 0
else
	for filename in logs/* 
	do
		echo "Output for $filename"
		cat $filename
	done
	exit $EXITCODE
fi
