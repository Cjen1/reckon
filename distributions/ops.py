from utils import link
from utils import message_pb2 as msg_pb
import random

def payload(num_bytes):
    return rand.bytes(num_bytes)

def write(key, value):
    op = msg_pb.Operation()
    op.put.key = key
    op.put.value = value

    payload = op.SerializeToString()

    return payload

def read(key):
    op = msg_pb.Operation()
    op.get.key = key

    payload = op.SerializeToString()

    return payload

def quit():
    op = msg_pb.Operation()
    op.quit.msg = "Quit"

    payload = op.SerializeToString()
    
    return payload
