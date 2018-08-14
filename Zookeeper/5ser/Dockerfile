FROM bash
FROM openjdk:7

ADD zkconfs /zkconf
ARG ZOO_MY_ID
RUN cd / ; \
    wget http://apache.mirror.anlx.net/zookeeper/stable/zookeeper-3.4.12.tar.gz; \ 
    tar xvf zookeeper-3.4.12.tar.gz; \
    mv zookeeper-3.4.12  /usr/local/zookeeper; \
    mkdir /usr/local/zookeeper/data; \
    mkdir /usr/local/zookeeper/logs; \
    cp /zkconf/zoo"$ZOO_MY_ID".cfg /usr/local/zookeeper/conf/zoo.cfg; \
    cp /zkconf/java.env /usr/local/zookeeper/conf/java.env; \
    echo "$ZOO_MY_ID" > /usr/local/zookeeper/data/myid
EXPOSE 2181 
EXPOSE 2888 
EXPOSE 3888
#ENV PATH=$PATH:/usr/lib/jvm/default-java/jre/lib
#CMD pwd; ls /usr/local/bin; echo $PATH
#CMD java -v
ENV ZKSTARTCMD "/usr/local/zookeeper/bin/zkServer.sh start-foreground ; cat /usr/local/zookeeper/logs/zookeeper.log"
#CMD "$ZKSTARTCMD"
#CMD bash export PATH=/usr/lib/jvm/default-java/jre/lib:$PATH; bash /usr/local/zookeeper/bin/zkServer.sh start-foreground
CMD bash /usr/local/zookeeper/bin/zkServer.sh start-foreground 

