import message_pb2 as msg_pb
import random
import time
import numpy.random as rand

def payload(num_bytes):
    return rand.bytes(num_bytes)

def write(key, value):
    start = time.time()
    op = msg_pb.Operation()
    op.put.key = key
    op.put.value = value
    op.put.start = start

    payload = op.SerializeToString()

    return payload

def read(key):
    start = time.time()
    op = msg_pb.Operation()
    op.get.key = key
    op.get.start = start

    payload = op.SerializeToString()

    return payload

def quit():
    op = msg_pb.Operation()
    op.quit.msg = "Quit"

    payload = op.SerializeToString()
    
    return payload
