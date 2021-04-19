FROM centos:centos7

RUN yum makecache && \
    yum install -y epel-release && \
    yum install -y unzip which wget curl
RUN yum install -y java-1.8.0-openjdk

RUN groupadd -g 1000 elasticsearch && \
    adduser -u 1000 -g 1000 -d /usr/share/elasticsearch elasticsearch

ENV ESVERSION 6.8.13
WORKDIR /usr/share/elasticsearch
ENV PATH /usr/share/elasticsearch/bin:$PATH
ENV ELASTICSEARCH_PATH /usr/share/elasticsearch/bin

#COPY elasticsearch-$ESVERSION.tar.gz /elasticsearch-$ESVERSION.tar.gz
RUN set -ex; \
        dir="$(dirname "$ELASTICSEARCH_PATH")"; \
        mkdir -p "$dir" ; \
    wget https://repo.huaweicloud.com/elasticsearch/$ESVERSION/elasticsearch-$ESVERSION.tar.gz -O /elasticsearch.tar.gz ; ls -alh /elasticsearch.tar.gz ;\
    tar -xf /elasticsearch.tar.gz --strip-components=1 -C "$dir" ; \
    rm -f /elasticsearch.tar.gz ; \
    chown elasticsearch.elasticsearch -R "$dir"/config "$dir"/logs

ENV ES_TMPDIR="/tmp"

COPY config/elasticsearch.yml /usr/share/elasticsearch/config/elasticsearch.yml
COPY docker-entrypoint.sh /
RUN sed -ie 's/ES_DISTRIBUTION_TYPE=tar/ES_DISTRIBUTION_TYPE=docker/' /usr/share/elasticsearch/bin/elasticsearch-env
RUN sed -ie 's/-Xms1g/#-Xms1g/' /usr/share/elasticsearch/config/jvm.options
RUN sed -ie 's/-Xmx1g/#-Xmx1g/' /usr/share/elasticsearch/config/jvm.options
RUN chmod +x /docker-entrypoint.sh
COPY Shanghai /etc/localtime
COPY curl.txt /

EXPOSE 9200 9300
ENV ES_JAVA_OPTS "-Xms1g -Xmx1g"
ENV MEMORY_LOCK true
ENV DIS_HOSTS "127.0.0.1"
ENV INIT_NODES "127.0.0.1" 
ENV DIS_NUMBER 1
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["elasticsearch"]
