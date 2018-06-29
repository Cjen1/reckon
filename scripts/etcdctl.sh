IP1=`dig +short caelum-504.cl.cam.ac.uk`
IP2=`dig +short caelum-505.cl.cam.ac.uk`
IP3=`dig +short caelum-506.cl.cam.ac.uk`

ETCDCTL_API=3 etcdctl --endpoints http://${IP1}:2379,http://${IP2}:2379,http://${IP3}:2379 $@
