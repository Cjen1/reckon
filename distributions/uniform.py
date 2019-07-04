import numpy.random as rand
import ops

def generate_ops(key_range='1>10',payload_size='10', n='10000', seed='0', write_ratio='0.5'):
    krl, kru = key_range.split(>)
    krl, kru = int(krl), int(kru)

    payload_size = int(payload_size)

    n=int(n)

    write_ratio = float(write_ratio)

    seed=int(seed)

    rand.seed(seed)
    return (
            lambda (): 
                ops.write(
                    rand.random_integers(krl, krh),
                    ops.payload(payload_size)
                ) 
                if rand.ranf() < write_ratio else
                ops.read(
                    rand.random_integers(krl, krh)
                )
            )




