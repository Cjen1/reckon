import threading
import numpy as np
import time
from subprocess import call
from op_gen import Operation

def NoFailure(ops):
    return [Operation.standard(op) for op in ops]

def SystemFailure(ops, endpoints):
    res = NoFailure(ops) 
    res += [Operation.system_failure(system_crash(endpoint)) for endpoint in endpoints]
    res += NoFailure(ops)
    return res

def SystemFailureRecovery(ops, endpoints):
    res = SystemFailure(ops, endpoints)
    res += [Operation.system_recovery(system_recovery(endpoint)) for endpoint in endpoints]
    res += NoFailure(ops)
    return res

def system_crash(endpoint):
    def helper(service):
        call(["scripts/" + service + "_stop.sh", endpoint], shell=True)
    return helper

def system_recovery(endpoint):
    def helper(service):
        call(["scripts/" + service + "_start.sh", endpoint], shell=True)
    return helper

