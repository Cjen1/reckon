#!/usr/bin/env bash

service openvswitch-switch start
ovs-vsctl set-manager ptcp:6640

python benchmark.py etcd_go \
  simple --topo_args n=1,nc=1 uniform --writ-ratio 1 none \
  --benchmark_config rate=1000,duration=10,dest=./res,logs=./logs `realpath .`

EXITCODE=$?

service openvswitch-switch stop

test $EXITCODE -eq 0 && exit 0 || exit 1
