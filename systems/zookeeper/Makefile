build: client

client: src/clients/java/Client.java protobuf
	javac -Xlint:deprecation -cp "src:jars/com.google.protobuf.jar:jars/com.neilalexander.jnacl.crypto.jar:jars/org.zeromq.jar:jars/slf4j.jar:jars/zookeeper-3.4.12.jar" -d build src/clients/java/Client.java

protobuf: ../../utils/message.proto
	protoc -I ../../utils --java_out src ../../utils/message.proto

