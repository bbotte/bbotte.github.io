FROM harbor.iris-technologies.com.cn:50505/devops/openjdk:8-alpine

ENV ZK_USER=root \
    ZK_DATA_DIR=/var/lib/zookeeper/data \
    ZK_DATA_LOG_DIR=/var/lib/zookeeper/log \
    ZK_LOG_DIR=/var/log/zookeeper \
    ZK_DIST=zookeeper-3.4.14 

RUN mkdir /opt
RUN set -x \
    && apk add wget bash --no-cache && rm -f /var/cache/apk/* \
    && wget "http://www.apache.org/dist/zookeeper/$ZK_DIST/$ZK_DIST.tar.gz" \
    && tar -xzf "$ZK_DIST.tar.gz" -C /opt \
    && rm -r  "$ZK_DIST.tar.gz" \
    && ln -s /opt/$ZK_DIST /opt/zookeeper 

# Create a user for the zookeeper process and configure file system ownership
# for necessary directories and symlink the distribution as a user executable
RUN set -x \
    && mkdir -p $ZK_DATA_DIR $ZK_DATA_LOG_DIR $ZK_LOG_DIR /usr/share/zookeeper /tmp/zookeeper /usr/etc/ 

EXPOSE 2181 2888 3888
COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
WORKDIR /opt/zookeeper
CMD ["./bin/zkServer.sh", "start-foreground"]
