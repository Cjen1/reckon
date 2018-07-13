#Given host names passed into script as args with ssh logins etc already set up
ETCD_VERSION=v3.3.8
DATA_DIR=/var/lib/etcd
CLUSTER_STATE=new
CLUSTER_TOKEN=urop-cluster-1
REGISTRY=gcr.io/etcd-development/etcd

if [ $# -eq 3 ]
then
	echo "-------- checking docker installed ----------"
	ssh $1 "sudo apt-get install docker.io -y"
	ssh $2 "sudo apt-get install docker.io -y"
	ssh $3 "sudo apt-get install docker.io -y"

	
	IP1=`dig +short $1`
	IP2=`dig +short $2`
	IP3=`dig +short $3`

	NAME_1=etcd-node-1
	NAME_2=etcd-node-2
	NAME_3=etcd-node-3
	CLUSTER="${NAME_1}=http://${IP1}:2380,${NAME_2}=http://${IP2}:2380,${NAME_3}=http://${IP3}:2380"

	#args: Name, IP
	run_remote(){
		THIS_NAME=$1
		THIS_IP=$2

		echo "screen -d -S etcd_background -m sudo docker run \
		  -p 2379:2379 \
		  -p 2380:2380 \
		  --name etcd ${REGISTRY}:${ETCD_VERSION} \
		  /usr/local/bin/etcd \
		  --data-dir=/etcd-data --name ${THIS_NAME} \
		  --initial-advertise-peer-urls http://${THIS_IP}:2380 --listen-peer-urls http://0.0.0.0:2380 \
		  --advertise-client-urls http://${THIS_IP}:2379 --listen-client-urls http://0.0.0.0:2379 \
		  --initial-cluster ${CLUSTER} \
		  --initial-cluster-state ${CLUSTER_STATE} --initial-cluster-token ${CLUSTER_TOKEN}"
	}

	echo "----------- start setup node $1 -------------"
	ssh $1 "sudo docker rm -f etcd; $(run_remote $NAME_1 $IP1)"

	echo "----------- start setup node $2 -------------"
	ssh $2 "sudo docker rm -f etcd; $(run_remote $NAME_2 $IP2)"

	echo "----------- start setup node $3 -------------"
	ssh $3 "sudo docker rm -f etcd; $(run_remote $NAME_3 $IP3)" 

else
	echo "Please enter 3 host names"
fi

	
