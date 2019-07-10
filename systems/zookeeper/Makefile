build: client

client: src/clients/java/Client.java protobuf
	javac -Xlint:deprecation -cp "src:service/jars/com.google.protobuf.jar:service/jars/com.neilalexander.jnacl.crypto.jar:service/jars/org.zeromq.jar:service/jars/slf4j.jar:service/jars/zookeeper-3.4.12.jar" -d build src/clients/java/Client.java

protobuf: ../../utils/message.proto
	protoc -I ../../utils --java_out src ../../utils/message.proto

