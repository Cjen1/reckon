from subprocess import call, Popen


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


def run_test(system='etcd', client='go', rate='1000', topo='simple', nn='3', nc='1', failure='none', tag='', duration='60'):
    tag = "sys_{sys}.cli_{cli}.rate_{rate}.topo_{topo}.nn_{nn}.nc_{nc}.fail_{failure}.dur_{duration}.{tag}".format(
        sys=system,
        cli=client,
        rate=rate,
        topo=topo,
        nn=nn,
        nc=nc,
        failure=failure,
        duration=duration,
        tag=tag
    )
    call_tcp_dump(
        tag,
        [
            "python",
            "benchmark.py",
            system,
            topo,
            "--number-nodes",
            nn,
            "--number-clients",
            nc,
            "uniform",
            failure,
            "--client",
            client,
            "--system_logs",
            "/results/logs",
            "--benchmark_config",
            (
                "rate={0},".format(rate)
                + "duration={0},".format(duration)
                + "test_results_location=/results/res_"
                + tag
                + ".res,"
                + "logs=/results/log_"
                + tag
                + ".log"
            ),
        ],
    )
    call(["bash", "scripts/clean.sh"])

for client in ['go', 'go-100', 'go-10000']:
    run_test(rate='20000', client=client)

## leader failure validation
#for rate in [1, 100, 1000]:
#    for client in ['go', 'go-100', 'go-10000']:
#        run_test(rate=rate, client=client, failure='leader')

#for repeat in range(3):
#    # Leader failure
#    run_test("etcd", "go-no-mem", 500, "simple", "3", "1", "leader", "repeat{0}_leader_failure".format(repeat), "60")
#
#    # Partial Partition No Memory
#    run_test("etcd", "go-no-mem", 500, "simple", "3", "1", "partial-partition", "repeat{0}_part_no_mem".format(repeat), "600", )
#
#    # Partial Partition 100 clients
#    run_test(
#        "etcd", "go", 500, "simple", "3", "1", "partial-partition", "repeat{0}_part_100_cli".format(repeat), "600"
#    )
#
#    # Partial Partition No Check Quorum
#    run_test(
#        "etcdNoCQ", "go", 500, "simple", "3", "1", "partial-partition", "repeat{0}_no_cq".format(repeat), "600"
#    )
#
#    # Intermittent partial partiion
#    run_test(
#        "etcd", "go", 500, "simple", "3", "1", "intermittent", "repeat{0}_intermittent".format(repeat), "600"
#    )
#
#
#    # WAN colocated
#    run_test("etcd", "go", 1000, "wan", "7", "1", "none", "repeat{0}_wan_7".format(repeat), "60")
