from subprocess import call
from sys import argv
from socket import gethostbyname

hosts = argv[1].split(",")

def setup_remote(host):
#    cluster = "".join("etcd-node-" + str(i+1) + "=http://" + host + ":2380," for i, host in enumerate(hosts))[:-1]
#    call(["cd ~/Zookeeper; bash zkstartupdate.sh; cd tester/scripts"])
    call([
        "ssh",
        host,
        (  "docker run -d " + 
            "-p 2181:2181 -p 2888:2888 -p 3888:3888 " +
            "--restart always " +
            "--name zookeeper {registry}:{zk_ver} " 
        ).format(
            registry="zkstart", 
            zk_ver="latest") 
        ])

call(["python", "scripts/zkCleanup.py"])

for host in hosts:
    setup_remote(host)

