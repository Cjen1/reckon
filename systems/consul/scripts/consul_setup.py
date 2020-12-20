from subprocess import call, Popen
from sys import argv
from socket import gethostbyname
import socket


def bootstrap(host, external_ip, hosts):
    call(
        [
            "ssh",
            host,
            (
                "docker run -d --name consul "
                + "--net=host "
                + "-p {external_ip}:8300:8300 "
                + "-p {external_ip}:8301:8301 "
                + "-p {external_ip}:8301:8301/udp "
                + "-p {external_ip}:8302:8302 "
                + "-p {external_ip}:8302:8302/udp "
                + "-p {external_ip}:8400:8400 "
                + "-p {external_ip}:8500:8500 "
                + "-p 172.17.0.1:53:53/udp "
                + "consul agent -server -bind {external_ip} -bootstrap-expect {num_serv}"
            ).format(external_ip=external_ip, num_serv=str(len(hosts))),
        ]
    )


def join(host, external_ip, first_ip, index):
    call(
        [
            "ssh",
            host,
            (
                "docker run -d --name consul "
                + "--net=host "
                + "-p {external_ip}:8300:8300 "
                + "-p {external_ip}:8301:8301 "
                + "-p {external_ip}:8301:8301/udp "
                + "-p {external_ip}:8302:8302 "
                + "-p {external_ip}:8302:8302/udp "
                + "-p {external_ip}:8400:8400 "
                + "-p {external_ip}:8500:8500 "
                + "-p 172.17.0.1:53:53/udp "
                + "consul agent -server -bind {external_ip} -join {first}"
            ).format(external_ip=external_ip, first=first_ip),
        ]
    )


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


def start_client_node(endpoints):
    localAddress = get_ip()
    call(
        [
            "sudo",
            "docker",
            "run",
            "-d",
            "--net=host",
            "-p",
            "8500:8500",
            "--name",
            "consul",
            "consul",
            "agent",
            "-bind=" + localAddress,
            "-retry-join=" + endpoints[0],
        ]
    )


hosts = argv[1].split(",")
host_ips = [gethostbyname(host) for host in hosts]
host_ips = [ip if not "127" in ip else get_ip() for ip in host_ips]

bootstrap(hosts[0], host_ips[0], hosts)
for i, host in enumerate(hosts[1:]):
    join(host, host_ips[i + 1], host_ips[0], i + 2)

start_client_node(host_ips)
