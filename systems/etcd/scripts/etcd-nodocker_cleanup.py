from subprocess import call
from sys import argv

def remove_remote(host):
    call(["ssh", host, "screen -X -S etcd_background quit"])
    call(["ssh", host, "rm -r *etcd*"])

hosts = argv[1].split(",")

for host in hosts:
    remove_remote(host)

