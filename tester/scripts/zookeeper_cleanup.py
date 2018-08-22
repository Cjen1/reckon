from subprocess import call
from sys import argv
def rmZK(host):
	call(["ssh", host, "docker rm -f zookeeper"])

hosts = argv[1].split(',')


for host in hosts[::-1]:
	rmZK(host)
