import zmq
import message_pb2 as msg_pb
import socket

class Link_Context:
    def __init__(self, port):
        self.port = port
        self.zmq_context = zmq.Context()

def send(link_context, message):
    socket = link_context.zmq_context.socket(zmq.REQ)
    binding = "tcp://127.0.0.1:" + link_context.port

    print("Awaiting endpoint connection on " + binding)
    socket.connect(binding)

    socket.send(message)

    print("Awaiting response on " + binding)
    return socket.recv()

def put(link_context, key, value):
    op = msg_pb.Operation()
    op.put.key = key
    op.put.value = value

    payload = op.SerializeToString()

    rec = send(link_context, payload)

    resp = msg_pb.Response()
    resp.ParseFromString(rec)

    return resp

def setup(link_context):
    hosts = ["caelum-504.cl.cam.ac.uk", "caelum-505.cl.cam.ac.uk", "caelum-506.cl.cam.ac.uk"]
    ips = [socket.gethostbyname(host) for host in hosts]

    op = msg_pb.Operation()
    op.setup.endpoints.extend([ip + ":2379" for ip in ips])

    payload = op.SerializeToString()
    rep = send(link_context, payload)

    resp = msg_pb.Response()
    resp.ParseFromString(rep)

    return resp

def close(link_context):
    op = msg_pb.Operation()
    op.quit.msg = "Quitting normally"

    payload = op.SerializeToString()
    rep = send(link_context, payload)

    resp = msg_pb.Response()
    resp.ParseFromString(rep)

    return resp

def gen_context(port):
    return Link_Context(port)
