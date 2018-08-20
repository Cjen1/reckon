from subprocess import call
from sys import argv

hosts = argv[1].split(",")

call(["python", "scripts/zookeeper" + len(hosts) + "_setup.py", argv[1]])
