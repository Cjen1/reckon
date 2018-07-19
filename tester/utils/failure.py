import threading
import numpy as np

class Stoppable_Thread(threading.Thread):
    def __init__(self):
        super(Stoppable_Thread, self).__init__()
        self.__stop_event = threading.Event()

    def stop(self):
        self.__stop_event.set()

    def stopped(self):
        return self.__stop_event.is_set()

def nofailure(name):
    return Failure_Thread(threading.Thread)

class Error_Simulator_Thread(Stoppable_Thread):
    def __init__(self, mtbf, mttr, hosts, client_name):
        super(self)
        self.mtbf = mtbf
        self.mttr = mttr
        self.hosts = hosts
        self.log = []

        #TODO execute correct script to stop and restart client 

    def run():
        while not self.stopped():
            # sleep for time T, where T is distributed given a constant failure rate => exponential function
            time.sleep(np.random.exponential(self.mtbf)) 

            self.log.append("Stopping service at " + time.now())
            # Possible security issue here, implied that command is 'trusted' though
            call(['ssh', self.hosts[np.random.randint(len(hosts))], self.start_command])
            
            # TODO make smarter repair function
            # sleep for time T, where T is distributed given a constant repair rate => exponential function
            time.sleep(np.random.exponential(self.mttr))


            self.log.append("Restarted service at " + time.now())
            call(['ssh', self.hosts[np.random.randint(len(hosts))], self.start_command])


none = (nofailure, nofailure)

def crashing_docker(mtbf, mttr, hosts, client_name):
    thread = Error_Simulator_Thread(mtbf, mttr, hosts)
    return (thread.start, thread.stop)
