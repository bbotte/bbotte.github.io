FROM openjdk:8-jre-alpine

ENV KAFKA_HOME=/opt/kafka
ENV PATH=${PATH}:${KAFKA_HOME}/bin

RUN mkdir /opt
COPY start-kafka.sh broker-list.sh create-topics.sh versions.sh /tmp/

RUN apk add --no-cache bash wget curl jq \ 
 && chmod a+x /tmp/*.sh \
 && mv /tmp/start-kafka.sh /tmp/broker-list.sh /tmp/create-topics.sh /tmp/versions.sh /usr/bin \
 && sync && wget http://mirrors.tuna.tsinghua.edu.cn/apache/kafka/2.3.0/kafka_2.11-2.3.0.tgz -O /tmp/kafka_2.11-2.3.0.tgz \
 && tar xfz /tmp/kafka_2.11-2.3.0.tgz -C /opt \
 && rm /tmp/kafka_2.11-2.3.0.tgz \
 && ln -s /opt/kafka_2.11-2.3.0 ${KAFKA_HOME} 

#RUN apk add --no-cache docker 
COPY overrides /opt/overrides

VOLUME ["/data"]

# Use "exec" form so that it runs as PID 1 (useful for graceful shutdown)
CMD ["start-kafka.sh"]
