from util import run_test
import itertools as it

def tests(folder_path):
    actions = []

    #systems = ['ocons-raft', 'ocons-conspire-leader', 'ocons-conspire-dc', 'ocons-conspire-leader-dc']
    #systems = ['ocons-conspire-leader-dc']
    systems = ['ocons-raft', 'ocons-conspire-leader', 'ocons-conspire-leader-dc']

    fd_timeouts = [0.01, 0.03, 0.06, 0.11, 0.21, 0.41]

    low_repeat = 5
    high_repeat = 50

    def low_jitter_topo(system):
        return {
            'topo':'wan',
            'nn': 3 if system in ['ocons-paxos', 'ocons-raft'] else 4,
            'delay':50,
            'system':system,
            'client':'ocaml',
            'tag':'low_jitter',
            }
    def high_jitter_topo(system):
        return low_jitter_topo(system) | {
                'jitter':0.1,
                'loss':0.01,
                'tag':'high_jitter',
                }

    # steady state erroneous election cost
    for (system, topo_gen, fd_timeout, repeat) in it.product(
        #systems,
        ['ocons-conspire-leader-dc'],
        [low_jitter_topo, high_jitter_topo],
        fd_timeouts,
        range(12),
        ):
        actions.append(
                lambda params = topo_gen(system) | {
                    'system':system,
                    'rate': 10000,
                    'failure_timeout':fd_timeout,
                    'delay_interval': 0.1,
                    'repeat':repeat,
                    'failure':'none',
                    'duration':10,
                    }:
                run_test(folder_path, params)
                )

    # leader failure singles
    for (system, repeat) in it.product(
            systems,
            range(low_repeat),
            ):
        actions.append(
                lambda params = low_jitter_topo(system) | {
                    'system':system,
                    'rate': 10000,
                    'failure_timeout':0.5,
                    'delay_interval': 0.1,
                    'repeat':repeat,
                    'failure':'leader',
                    'tcpdump':True,
                    'duration':10,
                    }:
                run_test(folder_path, params)
                )

    # leader failure bulk
    for (system, topo_gen, fd_timeout, repeat) in it.product(
            #systems,
            ['ocons-conspire-leader'],
            [low_jitter_topo, high_jitter_topo],
            #fd_timeouts,
            [0.01, 0.03],
            range(high_repeat),
            ):
        actions.append(
                lambda params = topo_gen(system) | {
                    'system':system,
                    'rate': 10000,
                    'failure_timeout':fd_timeout,
                    'delay_interval': 0.1,
                    'repeat':repeat,
                    'failure':'leader',
                    'tcpdump':False,
                    'duration':10,
                    }:
                run_test(folder_path, params)
                )

    # Bulk performance graphs
    for (system, rate, repeat) in it.product(
            systems,
            [20000, 40000, 60000, 80000, 100000, 120000, 140000],
            range(low_repeat),
            ):
        actions.append(
                lambda params = low_jitter_topo(system) | {
                    'system':system,
                    'rate': rate,
                    'failure_timeout':0.5,
                    'delay_interval': 0.1,
                    'repeat':repeat,
                    'failure':'none',
                    'tcpdump':False,
                    'duration':10,
                    }:
                run_test(folder_path, params)
                )

    return actions
