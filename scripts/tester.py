from subprocess import call, Popen
import numpy as np
from itertools import product

def call_tcp_dump(tag, cmd):
    tcp_dump_cmd = [
            'tcpdump', '-i', 'any',
            '-w', ('/results/pcap_'+tag+'.pcap'),
            'net', '10.0.0.0/16',
            '-n'
            ]
    print(tcp_dump_cmd)
    p = Popen(tcp_dump_cmd)
    call(cmd)
    p.terminate()

abs_path = '/root/mounted/Resolving-Consensus'

for rate in [1000]:#, 10000, 20000]:
    for n in [3]:
        system='ocaml-paxos_ocaml'
        tag = "{0}_{1}_{2}".format(n, rate, system)
        call_tcp_dump(
                tag,
                [
                    'python',
                    'benchmark.py',
                    system,
                    'simple',
                    '--topo_args', 
                    (
                        'n={0},nc=1'.format(n)
                    ),
                    'uniform',
                    '--dist_args',
                    (
                        'write_ratio=1'
                    ),
                    'none',
                    '--benchmark_config', 
                    (
                        'rate={0},'.format(rate) + 
                        'duration=30,'+
                        'dest=/results/res_'+tag+'.res,'+
                        'logs=/results/log_'+tag+'.log'
                    ),
                    abs_path,
                ]
            )
        call(['bash', 'scripts/clean.sh'])


#for rate in [10000,20000,30000,40000,50000]:
#    for n in [3]:
#        system='etcd_go'
#        tag = "{0}_{1}_{2}".format(n, rate, system)
#        call_tcp_dump(
#                tag,
#                [
#                    'python',
#                    'benchmark.py',
#                    system,
#                    'tree',
#                    '--topo_args', 
#                    (
#                        'n_clusters={0}'.format(n)
#                    ),
#                    'uniform',
#                    '--dist_args',
#                    (
#                        'write_ratio=1'
#                    ),
#                    'none',
#                    '--benchmark_config', 
#                    (
#                        'rate={0},'.format(rate) + 
#                        'duration=30,'+
#                        'dest=/results/res_'+tag+'.res,'+
#                        'logs=/results/log_'+tag+'.log'
#                    ),
#                    abs_path,
#                ]
#            )
#        call(['bash', 'scripts/clean.sh'])


#for i in range(1):
#    for failure in ['leader', 'follower']:
#        for rate in [40000]:
#            for n in [3]:
#                for system in ['etcd_go']:
#                    tag = "{0}_{1}_{2}_{3}_{4}.res".format(n, rate, system, failure, i)
#                    call_tcp_dump(
#                            tag,
#                            [
#                                'python',
#                                'benchmark.py',
#                                system,
#                                'simple',
#                                '--topo_args', 
#                                (
#                                    'n={0},nc=1'.format(n)
#                                ),
#                                'uniform',
#                                '--dist_args',
#                                (
#                                    'write_ratio=1'
#                                ),
#                                failure,
#                                '--benchmark_config', 
#                                    'rate={0},'.format(rate) + 
#                                    'duration=120,'+
#                                    'dest=/results/res_'+tag+'.res,'+
#                                    'logs=/results/log_'+tag,
#                                abs_path,
#                            ]
#                        )
#                    call(['bash', 'scripts/clean.sh'])
