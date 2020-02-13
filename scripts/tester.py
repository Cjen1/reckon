from subprocess import call
import numpy as np
from itertools import product

abs_path = '/root/mounted/Resolving-Consensus'

rate='10'
n = '3'
system='etcd_go'

#call(
#        [
#            'python',
#            'benchmark.py',
#            'etcd_go',
#            'simple',
#            '--topo_args', 
#            (
#                'n=3,nc=10'
#            ),
#            'uniform',
#            'none',
#            '--benchmark_config', 
#                'rate={0},'.format(10) + 
#                'duration=60,'+
#                'dest=../results/{0}_{1}_{2}.res,'.format(n, rate, system)+
#                'logs={0}_{1}_{2}_'.format(n,rate,system),
#            abs_path,
#            "-d"
#        ]
#    )

for rate in [4,16,64,256,1024,4000,10000,12000,14000,16000,18000,20000,32000,34000,36000,38000,40000,42000,44000,46000,48000,50000]:
    for n in [3]:
        for system in ['ocaml_paxos']:
            call(
                    [
                        'python',
                        'benchmark.py',
                        system,
                        'simple',
                        '--topo_args', 
                        (
                            'n=3,nc=1'
                        ),
                        'uniform',
                        '--dist_args',
                        (
                            'write_ratio=1'
                        ),
                        'none',
                        '--benchmark_config', 
                            'rate={0},'.format(rate) + 
                            'duration=60,'+
                            'dest=../results/{0}_{1}_{2}.res,'.format(n, rate, system)+
                            'logs={0}_{1}_{2}_'.format(n,rate,system),
                        abs_path,
                        "-d"
                    ]
                )
            call(['bash', 'scripts/clean.sh'])

'''
for rate in [4**exp for exp in [0,1,2,3,4,5,6]]:
    for n in [2**exp + 1 for exp in [1,2,3,4,5,6,7]]:
        for system in ['ocaml-paxos_ocaml','etcd_go','zookeeper_java']:
            call(
                    [
                        'python',
                        'benchmark.py',
                        system,
                        'simple',
                        '--topo_args', 'n={0},nc={1}'.format(n, 30),
                        'uniform',
                        'leader',
                        '--benchmark_config', 'rate={0},'.format(rate) + 
                        'duration=480,'+
                            'dest=../results/lf_{0}_{1}_{2}.res'.format(n, rate, system),
                        abs_path,
                        '-d'
                    ]
                )
            call(['bash', 'clean.sh'])
            '''
