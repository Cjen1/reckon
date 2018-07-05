import socket
import subprocess

def write(hosts):
    ips = [socket.gethostbyname(host) for host in hosts]
    sIPS = "https://" + str(ips[0]) + ":2379"
    for ip in ips[1:]:
        sIPS += ",https://" + str(ip) + ":2379"


    ress = subprocess.check_output("benchmark --endpoints=" + sIPS + " --target-leader --conns=1 --clients=1 put --key-space-size=100 --total=100 --val-size=256", shell=True) 

    print ress

write(["caelum-504.cl.cam.ac.uk", "caelum-505.cl.cam.ac.uk", "caelum-506.cl.cam.ac.uk"])





