from subprocess import call
from sys import argv

call("killall etcd client".split(" "))
call("rm -r utils/data/etcd*", shell=True)



