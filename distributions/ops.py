from utils import link
from utils import message_pb2 as msg_pb
import random

def payload(num_bytes):
    return rand.bytes(num_bytes)

def write(key, value, opid):
    op = msg_pb.Operation()
    op.put.key = key
    op.put.value = value
    op.put.opid = opid

    payload = op.SerializeToString()

    return payload

def read(key, opid):
    op = msg_pb.Operation()
    op.get.key = key

    op.put.opid = opid

    payload = op.SerializeToString()

    return payload

def quit():
    op = msg_pb.Operation()
    op.quit.msg = "Quit"

    payload = op.SerializeToString()
    
    return payload
