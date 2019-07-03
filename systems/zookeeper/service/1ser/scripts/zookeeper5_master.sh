#Given host names passed into script as args with ssh logins etc already set up
if [ $# -eq 3 ]
then
	PS1="$1.cl.cam.ac.uk"
	PS2="$2.cl.cam.ac.uk"
	PS3="$3.cl.cam.ac.uk"
	
	IP1=`dig +short $PS1`
	IP2=`dig +short $PS2`
	IP3=`dig +short $PS3`

	ZK_VERSION=3.4.12
	CLUSTER_STATE=new
	CLUSTER_TOKEN=urop-cluster-1
	NAME_1=1
	NAME_2=2
	NAME_3=3
	CLUSTER=${NAME_1}=http://${IP1}:2181:2888:3888,${NAME_2}=http://${IP2}:2181:2888:3888,${NAME_3}=http://${IP3}:2181:2888:3888
	#args: Name, IP, ID
	run_remote(){

#		echo "etcd --name $1 \
#			--initial-advertise-peer-urls http://${2}:2380 \
#			--listen-peer-urls http://${2}:2380 \
#			--listen-client-urls http://${2}:2380 \
#			--advertise-client-urls http://${2}:2380 \
#			--initial-cluster-token etcd-cluster-1 \
#			--initial-cluster M1=http://${IP1}:2380,M2=http://${IP2}:2380,M3=http://${IP3}:2380
#			--initial-cluster-state new"
		THIS_NAME=$1
		THIS_IP=$2

		echo docker run \
			-p 2181:2181 \
			-p 2888:2888 \
 			-p 3888:3888 \
			-d \
			-v ~/logs:/usr/local/zookeeper/logs \
			--restart always \
			--name zookeeper \
			zkstart:latest 
	}
	
	ssh $1 "sudo docker rm -f zookeeper; $(run_remote $NAME_1 $IP1)"
	ssh $2 "sudo docker rm -f zookeeper; $(run_remote $NAME_2 $IP2)"
	ssh $3 "sudo docker rm -f zookeeper; $(run_remote $NAME_3 $IP3)"
	

else
	echo "Please enter either 3 or 5 host names"
fi
