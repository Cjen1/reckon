zkuninstall(){
	if [ -d "/usr/local/zookeeper" ]
	then
		sudo rm -Rf /user/local/zookeeper
		echo uninstall
	else
		echo "no such file"
	fi
}

ssh caelum-508 "$(typeset -f zkuninstall); zkuninstall"
ssh caelum-507 "$(typeset -f zkuninstall); zkuninstall"
ssh caelum-506 "$(typeset -f zkuninstall); zkuninstall"
