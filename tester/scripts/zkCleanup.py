from subprocess import call
def rmZK(host):
	call(["ssh", host, "docker rm -f zookeeper"])

hosts = ["caelum-50{k}.cl.cam.ac.uk".format(k=str(i+4)) for i in range(5)]



for host in hosts[::-1]:
	rmZK(host)
