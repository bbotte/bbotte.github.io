FROM openjdk:8-alpine

ENV ZK_USER=root \
    ZK_DATA_DIR=/var/lib/zookeeper/data \
    ZK_DATA_LOG_DIR=/var/lib/zookeeper/log \
    ZK_LOG_DIR=/var/log/zookeeper \
    ZK_DIST=zookeeper-3.5.6

RUN mkdir /opt
RUN set -x \
    && apk add wget bash nmap shadow --no-cache && rm -f /var/cache/apk/* \
    && wget -q "http://www.apache.org/dist/zookeeper/$ZK_DIST/apache-$ZK_DIST-bin.tar.gz" \
    && tar -xzf "apache-$ZK_DIST-bin.tar.gz" -C /opt \
    && rm -r  "apache-$ZK_DIST-bin.tar.gz" \
    && ln -s /opt/apache-$ZK_DIST-bin /opt/zookeeper 

# Copy configuration generator script to bin
COPY zkGenConfig.sh zkOk.sh /opt/zookeeper/bin/

# Create a user for the zookeeper process and configure file system ownership
# for necessary directories and symlink the distribution as a user executable
RUN set -x \
   # && useradd $ZK_USER \
   # && [ `id -u $ZK_USER` -eq 1000 ] \
   # && [ `id -g $ZK_USER` -eq 1000 ] \
    && mkdir -p $ZK_DATA_DIR $ZK_DATA_LOG_DIR $ZK_LOG_DIR /usr/share/zookeeper /tmp/zookeeper /usr/etc/ \
   # && chown -R "$ZK_USER:$ZK_USER" /opt/zookeeper $ZK_DATA_DIR $ZK_LOG_DIR $ZK_DATA_LOG_DIR /tmp/zookeeper \
    && ln -s /opt/zookeeper/conf/ /usr/etc/zookeeper \
    && ln -s /opt/zookeeper/bin/* /usr/bin \
    && ln -s /opt/zookeeper/lib/* /usr/share/zookeeper

