#pyclient.py
#starts ping.py and Client.jar

from sys import argv
from threading import Thread
from subprocess import call

javacmd = ['java' , '-jar' , 'systems/zookeeper/clients/java/Client.jar' , argv[-3] , argv[-2] , argv[-1]]
pycmd = ['python' , 'systems/zookeeper/clients/java/bridge.py', argv[-1]]

javathread = Thread(target = lambda : call(javacmd))
pythread = Thread(target = lambda : call(pycmd))
pythread.setDaemon(True)
javathread.start()
pythread.start()
