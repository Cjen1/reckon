from subprocess import call
from sys import argv
from socket import gethostbyname

hosts = argv[1].split(",")
host_ips = [gethostbyname(host) for host in hosts]

def stop_remote(host):
	call(["ssh", host, "sudo docker rm -f consul"])

for i, host in enumerate(hosts):
	stop_remote(host)

def bootstrap(host, ip):
	call(["ssh",
	       host,
	       ("docker run -d -h node1 --name=consul " +
	        "-p {sip}:8300:8300 " +
		"-p {sip}:8301:8301 " +
		"-p {sip}:8301:8301/udp " +
		"-p {sip}:8302:8302 " +
		"-p {sip}:8302:8302/udp "+
		"-p {sip}:8400:8400 " + 
		"-p {sip}:8500:8500 " +
		"-p 172.17.0.1:53:53/udp " +
		"progrium/consul -server -advertise {sip} -bootstrap-expect {num_serv}"
	       ).format(
	        sip=ip,
		num_serv=str(len(hosts))
	       )
	     ])

def join(host, ip, first_ip, index):
	call(["ssh",
	       host,
	       ("docker run -d -h node" + str(index) + " --name=consul " +
	        "-p {sip}:8300:8300 " +
		"-p {sip}:8301:8301 " +
		"-p {sip}:8301:8301/udp " +
		"-p {sip}:8302:8302 " +
		"-p {sip}:8302:8302/udp "+
		"-p {sip}:8400:8400 " + 
		"-p {sip}:8500:8500 " +
		"-p 172.17.0.1:53:53/udp " +
		"progrium/consul -server -advertise {sip} -join {first}"
	       ).format(
	        sip=ip,
		first=first_ip
	       )
	     ])

def registrators():
	command = ""
	for i in range(len(host_ips)):
		command += ("docker rm -f registrator{index}; ").format(index=str(i+1))
	for host in hosts:
		call([
			"ssh",
			host,
			command
		])
	command = ""
	for i, host_ip in enumerate(host_ips):
		command += ("docker run -d --name=registrator{index} --net=host --volume=/var/run/docker.sock:/tmp/docker.sock gliderlabs/registrator:latest consul://{ip}:8500; "
		           ).format(index=str(i+1), ip=host_ip)
	for host in hosts:
		call([
			"ssh",
			host,
			command
		])

bootstrap(hosts[0], host_ips[0])
for i, host in enumerate(hosts[1:]):
	join(host, host_ips[i+1], host_ips[0], i+2)

registrators()
