from link import send
from struct import *
from numpy import random as rand
import math

def_put = '\x00'
def_get = '\x01'

# Number of keys to write, size of data in bytes
def sequentialKeys(number_keys, data_size):
    resp_times = []
    for i in range(number_keys):
        value = rand.randint(0, 255, data_size)

        # 'B' = unsigned byte
        c_value = array('B', value)

        key = i
        # 8 bytes long: 64 bit key
        c_key = to_bytes(key, 8)

        resp_time = put(c_key, c_value)
        resp_times.append(resp_time)

    return resp_times

def to_bytes(val, max_size):
    return 

def put(c_key, c_value):
    payload = array('B', def_put).extend(c_key).extend(c_value)

    return send(payload)
