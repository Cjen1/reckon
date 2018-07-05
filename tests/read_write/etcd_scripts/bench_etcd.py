import socket
import numpy as np
import etcd
from subprocess import call
import string

#Conflict ratio is the chance that two commands will touch the same key
def readgen(maxKeyValue, client):
    key = str(np.random.randint(maxKeyValue))
    return lambda : client.read(key)

def writegen(maxKeyValue, client):
    key = str(np.random.randint(maxKeyValue))
    value = np.random.uniform(0,10)
    return lambda : client.write(key, value)

def keygen(maxKeyValue, client):
    for i in range(maxKeyValue):
        client.write(str(i), 0)

def setup(hosts, maxKeyValue):
    print "--------- start etcd setup ------------------"

    script = "sh etcd_scripts/etcd_start.sh"
    for host in hosts:
        script += " " + host
    call(script, shell=True);
    
    ips = [socket.gethostbyname(host) for host in hosts]

    client = etcd.Client(host=tuple([(host, 2379) for host in hosts]), allow_reconnect=True)

    keygen(maxKeyValue, client)

    print "------------ end etcd setup -----------------"

    return client
    
