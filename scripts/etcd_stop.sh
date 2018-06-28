for var in "$@"
do
	ssh $var "sudo docker kill etcd; sudo docker rm etcd"
done
