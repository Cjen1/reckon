from subprocess import call
from sys import argv

call("rm -r utils/data/etcd*", shell=True)
