FROM centos:centos7
MAINTAINER matuoyi <bbotte@163.com>

# wget https://artifacts.elastic.co/downloads/kibana/kibana-6.2.2-x86_64.rpm
COPY kibana-6.2.2-x86_64.rpm /kibana-6.2.2-x86_64.rpm 
RUN  rpm -ivh /kibana-6.2.2-x86_64.rpm && \
    rm -f /kibana-6.2.2-x86_64.rpm && \
    sed -i 's@#server.host: "localhost"@server.host: "0.0.0.0"@' /etc/kibana/kibana.yml && \
    sed -i 's@#elasticsearch.url: "http://localhost:9200"@elasticsearch.url: "http://elasticsearch:9200"@' /etc/kibana/kibana.yml
 
ENV PATH /usr/share/kibana/bin:$PATH
ENV AUTHORIZED_KEYS **None**
RUN echo server.basePath: "/kibana" >> /etc/kibana/kibana.yml

COPY Shanghai /etc/localtime
COPY docker-entrypoint.sh /
RUN chmod +x /*.sh
 
EXPOSE 5601
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["kibana"]
