import link
from numpy import random as rand
import math

# Number of keys to write, size of data in bytes
def sequential_keys(port, number_keys, data_size):
    link_context = link.gen_context(str(port))
    # Set up servers etc
    link.setup(link_context)
    if number_keys > 256**4:
        print("Can't handle that many keys")
        return


    resp_times = []
    for i in range(number_keys):
        payload = rand.randint(0, 256**4, data_size)

        value = ""
        for i in payload:
            value += (str(i))

        key = i

        resp = link.put(link_context, key, value)
        
        if resp.err != "None":
            print("ERROR: " + resp.err)

        resp_times.append(resp.response_time)

    link.close(link_context)

    return resp_times

def linear_keys(link_context, number_keys, data_size):
    return

#link_context = link.gen_context("4444")
#print(sequential_keys(link_context, 100,4))
