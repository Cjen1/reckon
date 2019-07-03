# Just call each one individually like in the tester.py

from subprocess import call

hosts = ["caelum-50" + str(i) + ".cl.cam.ac.uk" for i in [4,5,6,7,8]]

arg_hostnames = ",".join(hosts)

call(["python", "scripts/" + 'zookeeper' + "_cleanup.py", arg_hostnames])
call(["python", "scripts/" + 'consul' + "_cleanup.py", arg_hostnames])
call(["python", "scripts/" + 'etcd' + "_cleanup.py", arg_hostnames])
