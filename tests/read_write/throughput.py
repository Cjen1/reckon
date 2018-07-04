import time
import numpy as np
import etcd/bench_etcd as b_etcd
import sys

class Concsys: pass

def bench_throughput(concsys):
    print "Generating operations"
    ratio, number = 1, 100
    ops = gen_ops(ratio, number, concsys.readgen, concsys.writegen)

    print "Starting throughput test"
    st = time.time()
    for op in ops:
        op()
    end = time.time()
    print "Finish throughput test"
    return len(ops) / (end - st)

def gen_ops(ratio, number, readgen, writegen):
    return [
            readgen() if i < ratio else writegen() 
            for i in np.random.uniform(0, 1, number)] 

def test_throughputs(number):
    print "-------- test throughput benchmark ----------"
    
    testsys = Concsys()
    testsys.readgen  = lambda : lambda : time.sleep(0.01)
    testsys.writegen = lambda : lambda : time.sleep(0.01)
    
    throughputs = [bench_throughput(testsys) for i in range(2)]
    
    return throughputs


def etcd_throughputs(number):
    print "-------- etcd throughput benchmark ----------"

    hosts = ["caelum-504.cl.cam.ac.uk", "caelum-505.cl.cam.ac.uk", "caelum-506.cl.cam.ac.uk"]

    maxKeyValue = 100

    client = b_etcd.setup(hosts, maxKeyValue)

    etcdsys = Concsys()
    etcdsys.readgen  =  lambda: b_etcd.readgen(maxKeyValue, client)
    etcdsys.writegen =  lambda: b_etcd.writegen(maxKeyValue, client)


    throughputs = [bench_throughput(etcdsys) for i in range(number)]

    return throughputs


if __name__ == "__main__":
    print etcd_throughputs(100)
