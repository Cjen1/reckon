REGISTRY=srg-urop-2018

build_docker() {
	THIS_NAME=$1
	THIS_IP=$2
	CLUSTER=$3

	echo "docker build \
		--build-arg CLUSTER=${CLUSTER} \
		--build-arg NAME=${THIS_NAME} \
		--build-arg IP=${THIS_IP} \
		-t ${REGISTRY}:${THIS_NAME}.latest \
		."
}

if [ $# -eq 3 ]
then
	

	ssh $1 "sudo apt-get install docker.io -y"
	ssh $2 "sudo apt-get install docker.io -y"
	ssh $3 "sudo apt-get install docker.io -y"

	IP1=`dig +short $1`
	IP2=`dig +short $2`
	IP3=`dig +short $3`

	NAME_1=$1
	NAME_2=$2
	NAME_3=$3
	
	CLUSTER="${NAME_1}:http://${IP1}:2380,${NAME_2}:http://${IP2}:2380,${NAME_3}:http://${IP3}:2380"

	$(build_docker $NAME_1 $IP1 $CLUSTER)
	$(build_docker $NAME_2 $IP2 $CLUSTER)
	$(build_docker $NAME_3 $IP3 $CLUSTER)

	for NAME in $NAME_1 $NAME_2 $NAME_3
	do
		mkdir images
		docker save -o images/${NAME}.tar.gz $REGISTRY:${NAME}.latest
		ssh $NAME mkdir ~/images
		scp ./images/${NAME}.tar.gz ${NAME}:~/images/docker_image.tar.gz
		ssh $NAME sudo docker load -i ~/images/docker_image.tar.gz
		ssh $NAME sudo rm -f ~/images/docker_image.tar.gz
	done
fi


