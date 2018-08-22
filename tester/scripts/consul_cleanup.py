from subprocess import call
from sys import argv

def rmCons(host):
	call(["ssh", host, "docker rm -f consul"])

def regs(host, reg):
	call(["ssh", host, "docker rm -f registrator{i}".format(i=reg)])


rs = [i+1 for i in range(5)]

hosts = argv[1].split(',')


for host in hosts[::-1]:
	rmCons(host)
	for r in rs:
		regs(host, r)
