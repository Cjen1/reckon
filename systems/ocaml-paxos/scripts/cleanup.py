from subprocess import call
from sys import argv

call("rm -r utils/data/ocaml*", shell=True)
call("killall ocaml-paxos-leader ocaml-paxos-acceptor ocaml-paxos-replica", shell=True)
