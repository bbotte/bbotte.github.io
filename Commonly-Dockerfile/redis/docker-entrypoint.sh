#!/bin/sh
set -e

if [ "$DATADIR" ];then
    sed -i "s#dir /data/redis#dir "$DATADIR"#" /etc/redis/redis.conf
    mkdir -p $DATADIR 
    echo "redis data dir is $DATADIR"
else
    mkdir -p /data/redis
    echo "redis data dir is /data/redis"
fi
echo -e "if redis is set slave, please set docker-compose.yaml \n  environment:\n    SLAVEIP: "172.17.1.101""
if [ "${MASTERIP}" ];then
    sed -i "281 aslaveof ${MASTERIP} 6379" /etc/redis/redis.conf
    sed -i 's/slave-read-only\ yes/slave-read-only\ no/' /etc/redis/redis.conf
    if [ "${PASSWD}" ];then
        sed -i "288 amasterauth ${PASSWD} " /etc/redis/redis.conf
    fi 
fi
if [ "${PASSWD}" ];then sed -i "500 arequirepass ${PASSWD} " /etc/redis/redis.conf;fi
if [ "${REDISCLUSTER}" ];then sed -i "814 acluster-enabled yes" /etc/redis/redis.conf;fi 
if [ "${USEAOF}" ];then sed -i "s/appendonly\ yes/appendonly\ ${USEAOF}/" /etc/redis/redis.conf;fi
# first arg is `-f` or `--some-option`
# or first arg is `something.conf`
if [ "${1#-}" != "$1" ] || [ "${1%.conf}" != "$1" ]; then
	set -- redis-server "$@"
fi

exec "$@"
