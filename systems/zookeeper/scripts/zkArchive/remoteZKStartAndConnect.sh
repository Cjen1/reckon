# Start all of the servers

ssh caelum-508 "sudo bash /usr/local/zookeeper/bin/zkServer.sh start"
ssh caelum-507 "sudo bash /usr/local/zookeeper/bin/zkServer.sh start"
ssh caelum-506 "sudo bash /usr/local/zookeeper/bin/zkServer.sh start"  

# Connect to each of the servers from caelum-505.

ssh caelum-505 "sudo bash /usr/local/zookeeper/bin/zkCli.sh -server 128.232.80.69:2181" #caelum-508
ssh caelum-505 "sudo bash /usr/local/zookeeper/bin/zkCli.sh -server 128.232.80.68:2181" #caelum-507
ssh caelum-505 "sudo bash /usr/local/zookeeper/bin/zkCli.sh -server 128.232.80.67:2181" #caelum-506

# Run commands from command line interface

ssh caelum-505 "sudo bash /usr/local/zookeeper/bin/zkCli.sh -server 128.232.80.67:2181 create /a 1" #Create a data node with name a, content 1 via caelum-505, over the server hosted on caelum-506
ssh caelum-505 "sudo bash /usr/local/zookeeper/bin/zkCli.sh -server 128.232.80.67:2181 delete /a"   #Create a data node with name a, content 1 via caelum-505, over the server hosted on caelum-506
