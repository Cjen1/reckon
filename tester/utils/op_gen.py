from utils import link
from utils import message_pb2 as msg_pb
from numpy import random as rand
import math


class Op: 
    type_OP = 0 
    type_NOP = 1 

    def __init__(self, op_type, operation = None, time = 0): 
        self.op_type = op_type
        if op_type == Op.type_NOP:
            self.time = time
        else:
            self.operation = operation

# Number of keys to write, size of data in bytes
def sequential_keys(number_keys, data_size):
    if number_keys > 256**4:
        print("Can't handle that many keys")
        return

    ops = []
    for key in range(number_keys):
        payload = rand.randint(0, 10, data_size)

        value = ""
        for i in payload:
            value += (str(i))

        ops.append(Op_put(key, value))

    return ops

def mixed_ops(num_ops, data_size, split, num_cli):	# split is the percentage as a double of reads.
    if num_ops > 256**4:
        print('Cannot handle that many keys. Aborting.')
        return

    num_keys = int(num_ops * (1 - split))
    num_reads = num_ops - num_keys
    
    wri = sequential_keys(num_keys, data_size)
    rea = []
    
    starti = num_keys 
    tmp = num_keys // num_cli

    
    for i in range(num_reads):
        key = rand.randint(0, tmp) * num_cli + ((starti + i) % num_cli)
	print("Generated read key: {k} at index {i}".format(k=str(key), i=str(starti + i)))
        rea.append(Op_get(key))
    
    res = wri
    res.extend(rea)

    return res

def Op_put(key, value):
    op = msg_pb.Operation()
    op.put.key = key
    op.put.value = value

    payload = op.SerializeToString()

    return Op(Op.type_OP, operation=payload)

def Op_get(key):
    op = msg_pb.Operation()
    op.get.key = key

    payload = op.SerializeToString()

    return Op(Op.type_OP, operation=payload)

def Op_quit():
    op = msg_pb.Operation()
    op.quit.msg = "Quit"

    payload = op.SerializeToString()

    return Op(Op.type_OP, operation=payload)
