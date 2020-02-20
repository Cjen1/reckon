import numpy.random as rand
import src.utils.ops as ops

def generate_prereqs(key_range='1>10'):
    krl, kru = [int(l) for l in key_range.split('>')]
    opl = []
    for k in range(krl, kru+1):
        op = ops.write(k, b'0', 0)
        op.op.prereq = True
        opl.append(op)

    return opl

def write(krl, kru, payload_size, start):
    op = ops.write(
                rand.random_integers(krl, kru),
                ops.payload(payload_size),
                start
                )
    op.op.prereq = False
    return op

def read(krl, kru, start):
    op = ops.read(
            rand.random_integers(krl, kru),
            start
            )
    op.op.prereq = False
    return op

def generate_ops(key_range='1>10',payload_size='10', seed='0', write_ratio='0.5'):
    krl, kru = key_range.split('>')
    krl, kru = int(krl), int(kru)

    payload_size = int(payload_size)

    write_ratio = float(write_ratio)

    seed= int(seed)

    return (
            generate_prereqs(key_range),
            (rand.seed(seed),
                lambda (start): (
                    write(krl, kru, payload_size, start)
                    if rand.ranf() < write_ratio else
                    read(krl, kru, start)
                    )
                )[-1]
            )
