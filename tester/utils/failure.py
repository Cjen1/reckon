import threading
import numpy as np
import time
from subprocess import call

def nofailure(name):
    return 

class Stoppable_Thread(threading.Thread):
    def __init__(self):
        super(Stoppable_Thread, self).__init__()
        self.__stop_event = threading.Event()

    def stop(self):
        self.__stop_event.set()

    def stopped(self):
        return self.__stop_event.is_set()

def stop_restart(mttr, stop, start, endpoint):
    print(stop, start)
    call([stop, endpoint], shell=True)
    
    # TODO make smarter repair function
    # sleep for time T, where T is distributed given a constant repair rate => exponential function
    time.sleep(np.random.exponential(mttr))

    call([start, endpoint], shell=True)
    

class Crash_Simulator_Thread(Stoppable_Thread):
    def __init__(self, mtbf, mttr, hosts, client_name):
        super(Crash_Simulator_Thread, self).__init__()
        self.mtbf = mtbf
        self.mttr = mttr
        self.hosts = hosts
        self.log = []

        self.start_script = "scripts/" + client_name + "_start.sh"
        self.stop_script = "scripts/" + client_name + "_stop.sh"

    def run(self):
        while not self.stopped():
            # sleep for time T, where T is distributed given a constant failure rate => exponential function
            time.sleep(np.random.exponential(self.mtbf)) 

            self.log.append("Stopping service at " + time.asctime())
            threading.Thread(target=stop_restart, 
                    args=(self.mttr, self.stop_script, self.start_script, self.hosts[np.random.randint(len(self.hosts))])
                        ).start()

def crash_sim_wrapper(mtbf, mttr, hosts, client_name):
    thread = Crash_Simulator_Thread(mtbf, mttr, hosts, client_name)
    return (thread.start, thread.stop)

def none(client_name):
    return (nofailure, nofailure)

def crash(mtbf, mttr, hosts):
    return lambda client_name: crash_sim_wrapper(mtbf, mttr, hosts, client_name)

