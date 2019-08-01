from subprocess import call

for n in [3]:
    call(
            [
                'python',
                'benchmark.py',
                'etcd_go',
                'simple',
                '--topo_args', 'n={0}'.format(n),
                'uniform',
                'none',
                '--benchmark_config', 
                    'rate=1,'+
                    'duration=360,'+
                    'dest=../results/servers_many_{0}.res'.format(n)
            ]
        )
