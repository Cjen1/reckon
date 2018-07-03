if [ $# -eq 3 ]
then
	for NAME in $1 $2 $3
	do
		ssh $NAME sudo docker rm -f etcd
		ssh $NAME sudo docker create --name etcd -p 2379:2379 -p 2380:2380 srg-urop-2018:$NAME.latest 
		ssh $NAME sudo docker start etcd
	done
else
	echo "Enter 3 nodes"
fi

