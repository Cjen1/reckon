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


def run_test(system, client, rate, topo, nn, nc, failure, tag, duration):
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


## Validation
#for rate in [1, 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000, 14000, 15000,16000, 17000, 18000, 19000, 20000]:
#    for n in [3,5,7]:
#        tag = "validation_{0}_{1}".format(n, rate)
#        run_test("etcd", "go", rate, "simple", str(n), "1", "none", tag, "60")
#

for repeat in range(3):
    # Leader failure
    run_test("etcd", "go-no-mem", 500, "simple", "3", "1", "leader", "repeat{0}_leader_failure".format(repeat), "60")

    # Partial Partition No Memory
    run_test("etcd", "go-no-mem", 500, "simple", "3", "1", "partial-partition", "repeat{0}_part_no_mem".format(repeat), "600", )

    # Partial Partition 100 clients
    run_test(
        "etcd", "go", 500, "simple", "3", "1", "partial-partition", "repeat{0}_part_100_cli".format(repeat), "600"
    )

    # Partial Partition No Check Quorum
    run_test(
        "etcdNoCQ", "go", 500, "simple", "3", "1", "partial-partition", "repeat{0}_no_cq".format(repeat), "600"
    )

    # Intermittent partial partiion
    run_test(
        "etcd", "go", 500, "simple", "3", "1", "intermittent", "repeat{0}_intermittent".format(repeat), "600"
    )


    # WAN colocated
    run_test("etcd", "go", 1000, "wan", "7", "1", "none", "repeat{0}_wan_7".format(repeat), "60")
