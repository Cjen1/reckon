from util import run_test
import itertools as it

def tests(folder_path):
    params = []

    reference_systems = ['ocons-paxos', 'ocons-raft', 'ocons-raft-pre-vote', 'ocons-raft+sbn', 'ocons-raft-pre-vote+sbn']
    industry_systems = ['etcd', 'zookeeper', 'zookeeper-fle', 'etcd-pre-vote', 'etcd+sbn', 'etcd-pre-vote+sbn']

    fd_timeouts = [0.01, 0.03, 0.06, 0.11, 0.21, 0.41, 0.81]

    low_repeat = range(3)
    high_repeat = range(25)

    def client_map(system):
        if 'ocons' in system:
            return 'ocaml'
        if 'etcd' in system:
            return 'go'
        if 'zookeeper' in system:
            return 'java'

    def low_jitter_topo(system):
        return {
            'topo':'wan',
            'nn': 5,
            'delay':50,
            'system':system,
            'client': client_map(system),
            'tag':'low_jitter',
            }

    def high_jitter_topo(system):
        return low_jitter_topo(system) | {
                'jitter':0.1,
                'loss':0.01,
                'tag':'high_jitter',
                }

    ## typical failure graphs
    #for system, repeat in it.product(
    #    reference_systems + industry_systems,
    #    low_repeat
    #    ):
    #    params.append(
    #            low_jitter_topo(system) | {
    #                'rate': 10000,
    #                'repeat': repeat,
    #                'duration': 10,
    #                'failure':'leader',
    #                'failure_timeout': 0.5,
    #                'tcpdump': True,
    #                'duration': 10,
    #                }
    #            )

    # TTR varying rate
    for rate, system, repeat in it.product(
        [1000, 4000, 16000],
        reference_systems + ['etcd', 'zookeeper', 'zookeeper-fle'],
        high_repeat,
        ):
        params.append(
                low_jitter_topo(system) | {
                    'rate': rate,
                    'repeat': repeat,
                    'failure': 'leader',
                    'failure_timeout': 0.5,
                    'duration': 10,
                    }
                )

    # TTR FD_timeout
    for fd_timeout, system, topo, repeat in it.product(
        fd_timeouts,
        reference_systems + industry_systems,
        [low_jitter_topo , high_jitter_topo],
        high_repeat,
        ):
        params.append(
                topo(system) | {
                    'rate': 10000,
                    'repeat': repeat,
                    'failure': 'leader',
                    'failure_timeout': fd_timeout,
                    'duration': 10,
                    }
                )

    for p in params:
        print(p)

    return [lambda p=p: run_test(folder_path, p) for p in params]
