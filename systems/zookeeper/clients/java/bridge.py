import zmq
from sys import argv

context = zmq.Context()
sock = context.socket(zmq.REQ)
loccont = zmq.Context()
locsock = loccont.socket(zmq.ROUTER)

sock.connect("ipc://"+argv[-1])

locsock.bind('tcp://127.0.0.1:10000')

while(True):
    addr, _ , ping = locsock.recv_multipart()
    sock.send(ping)
    pong = sock.recv_multipart()  # This blocks until we get something
    locsock.send_multipart([addr, b'', pong[-1]])
sock.close()
context.term()
