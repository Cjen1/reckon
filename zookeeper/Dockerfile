# For zk runtime
FROM openjdk:11

# For zk start scripts
FROM bash:4

# Add the zookeeper files to /zookeeper
ADD zookeeper-3.4.12 /zookeeper

ADD zoo.cfg /config/zoo.cfg

EXPOSE 2181
EXPOSE 2888
EXPOSE 3888

ENV DATA_SIZE 10737418240
ENV START_COMMAND 





