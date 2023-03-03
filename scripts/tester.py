from subprocess import call, Popen
import shlex
import itertools as it

def call_tcp_dump(tag, cmd):
    tcp_dump_cmd = [
        "tcpdump",
        "-i",
        "any",
        "-w",
        ("/results/pcap_" + tag + ".pcap"),
        "net",
        "10.0.0.0/16",
        "-n",
    ]
    print(tcp_dump_cmd)
    p = Popen(tcp_dump_cmd)
    call(cmd)
    p.terminate()


def run_test(
        system='etcd',
        client='go',
        topo='simple',
        failure='none',
        nn='3',
        nc='1',
        delay=0,
        loss="0",
        ncpr='False',
        mtbf='1',
        kill_n='0',
        write_ratio='1',
        rate='1000',
        duration='60',
        tag='tag',
        tcpdump=False,
        arrival_process='uniform',
        ):

    tag = ".".join([
        f"{system}.{topo}.{failure}.client_{client}",
        f"nn_{nn}.nc_{nc}.delay_{delay}.loss_{loss}",
        f"ncpr_{ncpr}.mtbf_{mtbf}",
        f"wr_{write_ratio}",
        f"rate_{rate}.duration_{duration}",
        f"process_{arrival_process}",
        f"{tag}",
        ])

    cmd = " ".join([
        f"python -m reckon {system} {topo} {failure}",
        f"--number-nodes {nn} --number-clients {nc} --client {client} --link-latency {delay} --link-loss {loss}",
        f"--new_client_per_request {ncpr}",
        f"--mtbf {mtbf} --kill-n {kill_n}",
        f"--write-ratio {write_ratio}",
        f"--rate {rate} --duration {duration}",
        f"--arrival-process {arrival_process}",
        f"--system_logs /results/logs --result-location /results/res_{tag}.res --data-dir=/data",
        ])

    print(f"Running: {cmd}")

    cmd = shlex.split(cmd)

    if tcpdump:
        call_tcp_dump(tag,cmd)
    else:
        call(cmd)

    call(["bash", "scripts/clean.sh"])

from numpy.random import default_rng
rng = default_rng()

actions = []
# Leader fault
# 20ms latency between nodes
# Aim to get throughput and mttr
for sys, repeat in it.product(
        [('etcd', 'go'), ('zookeeper', 'java')],
        range(10)
        ):
    system, client = sys
    actions.append(
            lambda repeat=repeat, system=system, client=client: run_test(
                failure="leader",
                system=system,
                client=client,
                delay=20,
                duration="30",
                tag = f"leader-repeat-{repeat}",
                tcpdump=True,
                )
            )

# Steady state
# Comparitive performance analysis of etcd and zookeeper
for sys, nn, rate, repeat in it.product(
        [('etcd', 'go'), ('zookeeper', 'java')],
        [1,3,5,7],
        [1000, 5000, 10000, 15000, 20000, 25000, 30000],
        range(3)
        ):
    system, client = sys
    actions.append(
        lambda system=system, client=client, nn=nn, rate=rate, repeat=repeat: run_test(
            system=system,
            client=client,
            nn=nn,
            delay=20,
            rate=rate,
            tag = f"steady-repeat-{repeat}",
            duration="30",
            )
        )

# Lossy steady state
# Comparative performance of etcd and zookeeper in a lossy environment
for sys, nn, linkloss, kill_n, repeat in it.product(
        [('etcd', 'go-tracer'), ('zookeeper', 'java')],
        [3,5,7],
        [0, 0.01, 0.1, 1, 10],
        [True, False],
        range(3)
        ):
    system, client = sys
    actions.append(
        lambda system=system, client=client, nn=nn, linkloss=linkloss, repeat=repeat, kill_n=kill_n: run_test(
            failure="kill-n",
            kill_n=nn/2 if kill_n else 0,
            topo='wan',
            system=system,
            client=client,
            nn=nn,
            delay=40,
            loss=linkloss,
            duration="30",
            arrival_process="poisson",
            tag = f"killed-{'max' if kill_n else 'none'}.lossy-steady-repeat-{repeat}",
            )
        )

# Lossy leader fault
# Leader election in a lossy environment
for sys, linkloss, repeat in it.product(
        [('etcd', 'go'), ('zookeeper', 'java')],
        [0.01, 0.1, 1],
        range(10)
        ):
    system, client = sys
    actions.append(
        lambda system=system, client=client, linkloss=linkloss, repeat=repeat: run_test(
            failure="leader",
            topo='wan',
            system=system,
            client=client,
            loss=linkloss,
            delay=40,
            duration="30",
            tag = f"lossy-leader-repeat-{repeat}",
            tcpdump=True
            )
        )

# wan performance
# Hoping for a nice stepwise graph :)
for sys in [('etcd', 'go'), ('zookeeper', 'java')]:
    system, client = sys
    actions.append(
        lambda system=system, client=client: run_test(
            topo='wan',
            system=system,
            client=client,
            delay=40,
            duration="30",
            tag = f"wan",
            )
        )


# Shuffle to isolate ordering effects
rng.shuffle(actions)

for act in actions:
    act()
