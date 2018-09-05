from subprocess import call
from sys import argv
from socket import gethostbyname

hosts = argv[1].split(",")

def setup_server(host, host_addr, master_addr):
    call([
        "ssh",
        host,
        (   "screen -d -S epaxos -m sudo docker run " +
            "-p 7089:7089 -p 7070:7070 " + 
            "-e MASTER_ADDR='{maddr}' " + 
            "-e ADDR='{haddr}' " + 
            "--name epaxos " + 
            "{registry}:{ep_ver} " + 
            "/bin/server " +
            "-maddr ${MASTER_ADDR} " + 
            "-addr ${ADDR} " +
            "-e " +
            "-durable " + 
            "-dreply " 
        ).format(
            registry="epaxos_svr",
            ep_ver="latest",
            maddr = master_addr,
            haddr = host_addr
            )
        ])

def setup_master(host, n_replicas):
    call([
        "ssh",
        host,
        (   "screen -d -S epaxos_master -m sudo docker run " +
            "-p 7089:7089


    
