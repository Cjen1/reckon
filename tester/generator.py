from link import send
from numpy import random as rand
import math

# Number of keys to write, size of data in bytes
def sequentialKeys(number_keys, data_size):
    if number_keys > 256**4:
        print("Can't handle that many keys")
        return

    resp_times = []
    for i in range(number_keys):
        value = rand.randint(0, 256**4, data_size)

        resp = link.put(key, value)
        
        # TODO get response time from protobuf
        if resp.err != "None":
            print(resp.err)

        resp_times.append(resp.response_time)

    return resp_times
