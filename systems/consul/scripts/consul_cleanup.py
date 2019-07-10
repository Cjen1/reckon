from subprocess import call
from sys import argv

def rmCons(host):
	call(["ssh", host, "docker rm -f consul"])

hosts = argv[1].split(',')

for host in hosts[::-1]:
	rmCons(host)

call(["sudo", "docker", "rm", "-f", "consul"])
call(["sudo", "docker", "volume", "prune", "-f"])
