import src.utils.message_pb2 as msg_pb
import random
import time
import numpy.random as rand


def payload(num_bytes):
    return rand.bytes(num_bytes)


def write(key, value, start):
    op = msg_pb.Request()
    op.op.put.key = key
    op.op.put.value = value
    op.op.start = start

    return op


def read(key, start):
    op = msg_pb.Request()
    op.op.get.key = key
    op.op.start = start

    return op
