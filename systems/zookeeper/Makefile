build: clientjar 
clientjar: client
	mkdir tmp; mkdir clients; mkdir clients/java;\
		cp src/clients/java/*.py clients/java;\
		cp src/clients/dockerfile clients/dockerfile;\
		cd tmp;\
		for f in ../jars/*; do echo $$f; jar -xvf $$f > log; done;\
		cp -r ../build/* .;\
		echo "Building .jar"; jar cvfe Client.jar clients.java.Client * > log;\
		mv Client.jar ../clients/java; \
		cd ..;\
		rm -r tmp

client: src/clients/java/Client.java buildfolder
	javac -Xlint:deprecation -cp "src:jars/junixsocket.jar:jars/juds.jar:jars/com.google.protobuf.jar:jars/org.zeromq.jar:jars/com.neilalexander.jnacl.crypto.jar:jars/slf4j.jar:jars/zookeeper-3.4.12.jar" -d build src/clients/java/Client.java

protobuf: ../../utils/message.proto
	protoc -I ../../utils --java_out src ../../utils/message.proto

docker: dockerfile
	docker build -t cjj39_dks28/zookeeper .

client_docker: clientjar clients/dockerfile
	docker build -t cjj39_dks28/zookeeper_clients clients

buildfolder:
	mkdir -p build
