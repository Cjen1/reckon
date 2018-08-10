zkinstall(){
	sudo apt-get install default-jdk #get newest java
	if [ -e "zookeeper-3.4.12.tar.gz" ]
       	then
		sudo rm -Rf zookeeper-3.4.12.tar.*
	fi
	sudo wget http://apache.mirror.anlx.net/zookeeper/stable/zookeeper-3.4.12.tar.gz #get source file
	#unpack source file and move to correct directory
	tar xvf zookeeper-3.4.12.tar.gz
	if [ -e "/usr/local/zookeeper" ]
	then
		sudo rm -rf /usr/local/zookeeper
	fi
	sudo mv zookeeper-3.4.12  /usr/local/zookeeper
	# make sure that zoo.cfg is in /usr/local/zookeeper/conf
	#make sure that java.env is in /usr/local/zookeeper/conf
	if [ -e "/usr/local/zookeeper/data" ]
	then
		sudo rm -rf /usr/local/zookeeper/data
	fi
	sudo mkdir /usr/local/zookeeper/data
	if [ -e "/usr/local/zookeeper/logs" ]
	then
		sudo rm -rf /usr/local/zookeeper/logs
	fi
	sudo mkdir /usr/local/zookeeper/logs
}

putconfig(){
	scp zkconfs/zoo$1-$2.cfg $2:/usr/local/zookeeper/conf/zoo.cfg
	scp zkconfs/java.env $2:/usr/local/zookeeper/conf/java.env
	ssh $2 "sudo bash -c 'echo $1 > /usr/local/zookeeper/data/myid'"
}

ssh caelum-508 "$(typeset -f zkinstall); zkinstall"
ssh caelum-507 "$(typeset -f zkinstall); zkinstall"
ssh caelum-506 "$(typeset -f zkinstall); zkinstall"

putconfig 1 caelum-508
putconfig 2 caelum-507
putconfig 3 caelum-506
