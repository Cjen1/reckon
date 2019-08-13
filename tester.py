from subprocess import call
import numpy as np
from itertools import product

abs_path = '/home/cjj39/mounted/Resolving-Consensus/'


"""
for n, r, nc in product([5], [1], [5]):
    call(
            [
                'python',
                'benchmark.py',
                'zookeeper_java',
                'simple',
                '--topo_args', 'n={0},nc={1}'.format(n, nc),
                'uniform',
                'none',
                '--benchmark_config', 
                    'rate={r},'.format(r=r) +
                    'duration=3600,'+
                    'dest=../results/zk_lf_{n}s_{nc}cli_r{r}.res'.format(n=n, r=r, nc=nc),
                abs_path
            ]
        )

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
                    'dest=../results/zk_{n}s_{nc}cli_r{r}.res'.format(n=n, r=r, nc=nc),
                abs_path
            ]
        )
"""
for n in [2**i+1 for i in range(1,5)]:
    for rate in sorted(set([int(i) for i in np.logspace(5,5.5,15,base=2)])):
        call(
                [
                    'python',
                    'benchmark.py',
                    'etcd_go',
                    'simple',
                    '--topo_args', 'n={0},nc={1}'.format(n, 1),
                    'uniform',
                    'none',
                    '--benchmark_config', 'rate={0},'.format(rate) + 
                        'duration=60,'+
                        'dest=../results/{0}_{1}_zk.res'.format(n, rate),
                    abs_path
                ]
            )

