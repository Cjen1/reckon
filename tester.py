from subprocess import call
import numpy as np
from itertools import product

for n, r, nc in product([3, 5, 13], sorted(set(int(x) for x in np.logspace(0,2,num=15,base=10))),[1,5,20]):
    call(
            [
                'python',
                'benchmark.py',
                'zookeeper_java',
                'simple',
                '--topo_args', 'n={0}'.format(n),
                'uniform',
                'none',
                '--benchmark_config', 
                    'rate={r},'.format(r=r) +
                    'duration=180,'+
                    'dest=../results/zk_{n}s_{nc}cli_r{r}.res'.format(n=n, r=r, nc=nc)
            ]
        )
