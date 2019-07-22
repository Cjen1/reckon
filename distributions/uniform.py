import numpy.random as rand
import ops

def generate_ops(key_range='1>10',payload_size='10', seed='0', write_ratio='0.5'):
    krl, kru = key_range.split('>')
    krl, kru = int(krl), int(kru)

    payload_size = int(payload_size)

    write_ratio = float(write_ratio)

    seed=int(seed)

    return (
            generate_prereqs(key_range),
            (rand.seed(seed),
                lambda  : (
                    ops.write(
                        rand.random_integers(krl, kru),
                        ops.payload(payload_size),
                        )
                         
                    if rand.ranf() < write_ratio else
                    ops.read(
                        rand.random_integers(krl, kru)
                        )
                         
                    )
                )[-1]
            )

def generate_prereqs(key_range='1>10'):
    krl, kru = [int(l) for l in key_range.split('>')]
    return [ops.write(k, b'0') for k in range(krl, kru+1)]	


