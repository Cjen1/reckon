from subprocess import call
from sys import argv

test_name = argv[1]

call(["ssh", "caelum-508", "docker logs zookeeper", "&>", "logs/" + test_name + "_zookeeper.logs"])
