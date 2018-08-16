from subprocess import call
def rmCons(host):
	call(["ssh", host, "docker rm -f consul"])

def regs(host, reg):
	call(["ssh", host, "docker rm -f registrator{i}".format(i=reg)])


rs = [i+1 for i in range(5)]
hosts = ["caelum-50{k}.cl.cam.ac.uk".format(k=str(i+4)) for i in range(5)]



for host in hosts[::-1]:
	rmCons(host)
	for r in rs:
		regs(host, r)
