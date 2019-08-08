import zmq
from sys import argv

print("PYCLIENT: pinging")
"""Sends ping requests and waits for replies."""
context = zmq.Context()
sock = context.socket(zmq.REQ)
loccont = zmq.Context()
locsock = loccont.socket(zmq.ROUTER)
print("PYCLIENT: Connecting to ipc://"+argv[-1])
sock.connect("ipc://"+argv[-1])
print("PYCLIENT: Looping back to localhost.")
locsock.bind('tcp://127.0.0.1:10000')
print('PYCLIENT: Connected.')
while(True):
    print('Pinging')
    addr, _ , ping = locsock.recv_multipart()
    print('PYCLIENT: Received Ping: ' + str(ping))
    sock.send(ping)
    pong = sock.recv_multipart()  # This blocks until we get something
    print('PYCLIENT: Recieved Pong: ' + str(pong))
    locsock.send_multipart([addr, b'', pong[-1]])
sock.close()
context.term()
