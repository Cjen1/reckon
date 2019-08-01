from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel

def setup(dockers, ips):
	cluster_infos = ['\n'.join(
				[
					'server.{zkid}='.format(zkid=i+1) + (ips[i] if (not i == k) else '0.0.0.0') + ':2888:3888'
					for i in range(len(dockers))
				]
			) for k in range(len(ips))]
	their_ids = [i + 1 for i in range(len(ips))]

	for d, info in zip(dockers, cluster_infos):
		d.cmd("echo {info} >> /usr/local/zookeeper/conf/zoo.cfg".format(info=info))
	
	for d, zkid in zip(dockers, their_ids):
		d.cmd("echo {zkid} > /usr/local/zookeeper/data/myid".format(zkid=zkid))

	restarters = []
	for docker in dockers:
		start_cmd = 'bash /usr/local/zookeeper/bin/zkServer.sh start-foreground'
		docker.cmd(start_cmd)
		restarters.append(lambda : docker.cmd(start_cmd))
	
	return restarters
