from subprocess import call
import numpy as np
from itertools import product

abs_path = '/root/mounted/Resolving-Consensus'


"""
for n, r, nc in product([5], [1], [5]):
    call(
            [
                'python',
                'benchmark.py',
                'etcd_go',
                'simple',
                '--topo_args', 'n={0},nc={1}'.format(n, nc),
                'uniform',
                'none',
                '--benchmark_config', 
                    'rate={r},'.format(r=r) +
                    'duration=60,'+
                    'dest=../results/{n}s_{nc}cli_r{r}.res'.format(n=n, r=r, nc=nc),
                abs_path
            ]
        )

for n in xrange(24, 27, 1):
    for rate in (np.log2(np.linspace(2, 256, num=13))**(1.7))[9:]:
        for system in ['zookeeper_java', 'etcd_go']:
            call(
                    [
                        'python',
                        'benchmark.py',
                        system,
                        'tree',
                        '--topo_args', 'n={0},nc=15'.format(n),
                        'uniform',
                        'none',
                        '--benchmark_config', 
                        'rate={r},'.format(r=rate)+
                        'duration=60,'+
                        'dest=../results/tree_{n}_{r}_{s}.res'.format(n=n,r=rate, s=system),
                        abs_path
                    ]
                )

"""
for rate in [3]:
    for n in [21]:#xrange(7, 37, 2):
        for system in ["zookeeper_java", 'etcd_go']: #'zookeeper_java']:
            call(
                    [
                        'python',
                        'benchmark.py',
                        system,
                        'tree',
                        '--topo_args', 'n={0},nc={1}'.format(n, 30),
                        'uniform',
                        'leader',
                        '--benchmark_config', 'rate={0},'.format(rate) + 
                        'duration=480,'+
                            'dest=../results/lf_{0}_{1}_{2}.res'.format(n, rate, system),
                        abs_path
                    ]
                )
            call(['bash', 'clean.sh'])
"""
for n in [5]:
    for rate in [2,3,4]:
        call(
                [
                    'python',
                    'benchmark_local.py',
                    'zookeeper_java',
                    'simple',
                    '--topo_args', 'n={0},nc={1}'.format(n, 20),
                    'uniform',
                    'none',
                    '--benchmark_config', 'rate={0},'.format(rate) + 
                        'duration=120,'+
                        'dest=../results/{0}_{1}_etcd_verification.res'.format(n, rate),
                        '-d',
                    abs_path
                ]
            )
"""
