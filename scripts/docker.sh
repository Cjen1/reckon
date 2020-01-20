#mininet start stuff
service openvswitch-switch start
ovs-vsctl set-manager ptcp:6640

bash scripts/run.sh

#mininet shutdown stuff
service openvswitch-switch stop
