import time
from pathlib import Path
from shutil import copyfile
import os
from subprocess import call, check_output
from tqdm import tqdm as tqdm
from sys import argv
import tarfile as tf


def start_servers(num_servers, zoo_src):
    for k in range(num_servers):
        zkd = "{zs}/".format(k=k, zs=zoo_src)
        zkkd = "{zs}{k}/".format(k=k, zs=zoo_src)
        cmd = "screen -d -m -S zk{k} bash {zkd}{bn} start-foreground {zkd}conf/zoo{k}.cfg".format(
            k=k, bn="bin/zkServer.sh", zkd=zkd
        )
        print(cmd)
        call(cmd.split(" "))


def finish_config(num_servers, zoo_src):
    # Assume that conf_src contains exactly one copy of zoo.cfg at the start, with no cluster info
    cluster_infos = [
        "server.{zkid}=".format(zkid=i + 1)
        + "localhost"
        + ":{0}:{1}".format(2888 + i, 3888 + i)
        for i in range(num_servers)
    ]

    their_ids = range(1, num_servers + 1)

    for k in tqdm(range(num_servers)):
        conf_file = "/conf/zoo{k}.cfg".format(k=k)
        data_dir = "/data-{k}/".format(k=k)
        myid = open("{zs}{dd}myid".format(dd=data_dir, zs=zoo_src), "w+")
        myid.write(str(k + 1))
        myid.close()
        conf = open("{zs}{cf}".format(cf=conf_file, zs=zoo_src), "a")
        conf.write("clientPort={cp}\n".format(cp=2181 + k))
        conf.write("dataDir={zs}{dd}\n".format(dd=data_dir, zs=zoo_src))
        for i, info in enumerate(cluster_infos):
            conf.write(info + "\n")
        conf.close()


def copy_install(num_servers, zoo_src, res_cons_dir):
    copyfile(
        "{rc}/systems/zookeeper/zkconfs/java.env".format(rc=res_cons_dir),
        "{zs}/conf/java.env".format(zs=zoo_src),
    )  # cp {rc}/systems/zookeeper/zkconfs/java.env {zd}/conf/java.env
    for k in tqdm(range(num_servers)):
        data_dir = "{zs}/data-{k}".format(k=k, zs=zoo_src)
        conf_file = "{zs}/conf/zoo{k}.cfg".format(k=k, zs=zoo_src)
        os.mkdir(data_dir)
        copyfile(
            "{rc}/systems/zookeeper/zkconfs/zoo_local.cfg".format(rc=res_cons_dir),
            conf_file,
        )  # cp {rc}/systems/zookeeper/zkconfs/zoo_local.cfg {zd}/conf/zoo.cfg


def orig_install(res_cons_dir, zoo_dest):
    commands = list(
        map(
            lambda s: s.split(" "),
            """wget http://apache.mirror.anlx.net/zookeeper/stable/apache-zookeeper-3.5.5-bin.tar.gz -O {zd}/apache-zookeeper-3.5.5-bin.tar.gz
mv {zd}/apache-zookeeper-3.5.5-bin/* {zd}
         """.format(
                rc=res_cons_dir, zd=zoo_dest
            ).split(
                "\n"
            ),
        )
    )
    print(commands[0])
    while "failure" in check_output(commands[0]):
        print("wget failed...")
    tf.open(
        "{zd}/apache-zookeeper-3.5.5-bin.tar.gz".format(zd=zoo_dest), "r:gz"
    ).extractall(zoo_dest)
    print(" ".join(commands[1]))
    for f in os.listdir("{zd}/apache-zookeeper-3.5.5-bin/".format(zd=zoo_dest)):
        os.rename(
            "{zd}/apache-zookeeper-3.5.5-bin/{f}".format(zd=zoo_dest, f=f),
            "{zd}/{f}".format(zd=zoo_dest, f=f),
        )
    os.mkdir("{zd}/data".format(zd=zoo_dest))
    copyfile(
        "{rc}/systems/zookeeper/zkconfs/zoo_local.cfg".format(rc=res_cons_dir),
        "{zd}/conf/zoo.cfg".format(zd=zoo_dest),
    )  # cp {rc}/systems/zookeeper/zkconfs/zoo_local.cfg {zd}/conf/zoo.cfg
    copyfile(
        "{rc}/systems/zookeeper/zkconfs/java.env".format(rc=res_cons_dir),
        "{zd}/conf/java.env".format(zd=zoo_dest),
    )  # cp {rc}/systems/zookeeper/zkconfs/java.env {zd}/conf/java.env
    Path("{zd}/data/myid".format(zd=zoo_dest)).touch()


if __name__ == "__main__":
    n = int(argv[-3])
    rc = argv[-2]
    base = argv[-1]
    zoo = base + "/usr/local/zookeeper"
    call(["mkdir", "-p", base + "/usr"])
    call(["mkdir", "-p", base + "/usr/local"])
    call(["mkdir", "-p", base + "/usr/local/zookeeper"])
    print("installing zookeeper")
    orig_install(rc, zoo)
    print("copying installation")
    copy_install(n, zoo, rc)
    print("finishing config")
    finish_config(n, zoo)
    print("starting servers")
    start_servers(n, zoo)
