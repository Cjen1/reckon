import threading
import numpy as np
import time
from subprocess import call
from op_gen import Operation

NOFAIL = "nofail"
def no_fail():
    return (NOFAIL, lambda *args: None)

FOLLOWER_CRASH = "crash"
def system_follower_crash(cluster):
    def helper(service, store_fail_fn):
        st = time.time()
        cluster_arg = "".join(host + ',' for host in cluster)[:-1]
        call(['python', 'scripts/'+service+'_stop.py', '--cluster', cluster_arg])
        end =time.time()
        store_fail_fn(FOLLOWER_CRASH, st, end)
    return (FOLLOWER_CRASH, helper)

LEADER_CRASH="leader_crash"
def system_leader_crash(cluster):
    def helper(service, store_fail_fn):
        st = time.time()
        cluster_arg = "".join(host + ',' for host in cluster)[:-1]
        call(['python', 'scripts/'+service+'_stop.py', '--cluster', cluster_arg, '-l'])
        end =time.time()
        store_fail_fn(LEADER_CRASH, st, end)
    return (LEADER_CRASH, helper)

RECOVER = "recover"
def system_recovery(endpoint):
    def helper(service, store_fail_fn):
        st = time.time()
        cluster_arg = endpoint
        call(["python", "scripts/"+service+"_start.py", "--cluster", cluster_arg])
        end = time.time()
        store_fail_fn(RECOVER, st, end)
    return (RECOVER, helper)

FULL_RECOVER = "full_recover"
def system_full_recovery(cluster):
    def helper(service, store_fail_fn):
        st = time.time()
        cluster_arg = "".join(host + ',' for host in cluster)[:-1]
        call(["python", "scripts/"+service+"_start.py", "--cluster", cluster_arg])
        end = time.time()
        store_fail_fn(FULL_RECOVER, st, end)
    return (FULL_RECOVER, helper)
