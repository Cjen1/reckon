import zmq
import lib_pb.message_pb2 as msg_pb

def send(context, port, message):
    socket = context.socket(zmq.REP)
    socket.bind("127.0.0.1:" + port)

    socket.send(message)

    return socket.recv()

def put(context, port, key, value):
    op = msg_pb.Operation()
    op.put.key = key
    op.put.value = value

    payload = op.SerializeToString()

    return op.ParseFromString(send(context, port, payload))
