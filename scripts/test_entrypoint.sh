#!/usr/bin/env bash

set -x

run_command () {
	service openvswitch-switch start
	ovs-vsctl set-manager ptcp:6640

	timeout 30 $@

	EXITCODE=$?

	service openvswitch-switch stop

	if [ $EXITCODE -eq 0 ]
	then 
		return 0
	else
		for filename in logs/* 
		do
			echo "Output for $filename"
			cat $filename
		done
		exit $EXITCODE
	fi
}
run_command "python benchmark.py etcd --client go simple --number-nodes 3 --number-clients 1 uniform --write-ratio 0.5 none --rate 1000 --duration 10 --result-location /results/etcd.res"

run_command "python benchmark.py ocons-paxos --client ocaml simple --number-nodes 3 --number-clients 1 uniform --write-ratio 0.5 none --rate 1000 --duration 10 --result-location /results/ocons.res"

pip install pandas

python scripts/throughput.py /results/*.res 

exit 0
