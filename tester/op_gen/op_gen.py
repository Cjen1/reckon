import link
from numpy import random as rand
import math

# Number of keys to write, size of data in bytes
def sequential_keys(link_context, number_keys, data_size):
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
            print(resp.err)

        resp_times.append(resp.response_time)

    link.close(link_context)

    return resp_times

link_context = link.gen_context("4444")
link.setup(link_context)
print(sequential_keys(link_context, 100,4))
