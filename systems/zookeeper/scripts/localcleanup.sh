for i in $(seq 0 $(( $1 - 1 )));
do screen -X -S zk$i quit;
	echo zk$i
done

rm -rf $2/*
