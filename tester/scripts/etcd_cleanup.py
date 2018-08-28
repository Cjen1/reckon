from subprocess import call
from sys import argv

def remove_remote(host):
    call(["ssh", host, "sudo docker rm -f etcd"])
    call(["ssh", host, "sudo docker volume prune -f"])

hosts = argv[1].split(",")

for host in hosts:
    remove_remote(host)

