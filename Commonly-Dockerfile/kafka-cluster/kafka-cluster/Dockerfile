FROM openjdk:8-jre-alpine

ENV KAFKA_HOME=/opt/kafka
ENV PATH=${PATH}:${KAFKA_HOME}/bin

RUN mkdir /opt

RUN apk add --no-cache bash wget \ 
 && wget http://mirrors.tuna.tsinghua.edu.cn/apache/kafka/2.3.0/kafka_2.11-2.3.0.tgz -O /tmp/kafka_2.11-2.3.0.tgz \
 && tar xfz /tmp/kafka_2.11-2.3.0.tgz -C /opt \
 && rm /tmp/kafka_2.11-2.3.0.tgz \
 && ln -s /opt/kafka_2.11-2.3.0 ${KAFKA_HOME} \
 && rm -rf /opt/kafka/site-docs

WORKDIR /opt/kafka
