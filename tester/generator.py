from link import send
from struct import *
from numpy import random as rand
import math
import lib_pb.operation_pb2 as op_pb

# Number of keys to write, size of data in bytes
def sequentialKeys(number_keys, data_size):
    if number_keys > 256**4:
        print("Can't handle that many keys")
        return

    resp_times = []
    for i in range(number_keys):
        value = rand.randint(0, 256**4, data_size)

        resp_time = put(key, value)
        resp_times.append(resp_time)

    return resp_times

def put(key, value):
    op = op_pb.Operation()
    
    op_setup

    return send(payload)
