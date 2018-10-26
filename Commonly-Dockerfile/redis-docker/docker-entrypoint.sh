#!/bin/sh
set -e

if [ "$DATADIR" ];then
    sed -i "s#dir /data/redis#dir "$DATADIR"#" /etc/redis.conf
    mkdir -p $DATADIR 
    echo "redis data dir is $DATADIR"
else
    mkdir -p /data/redis
    echo "redis data dir is /data/redis"
fi

# first arg is `-f` or `--some-option`
# or first arg is `something.conf`
if [ "${1#-}" != "$1" ] || [ "${1%.conf}" != "$1" ]; then
	set -- redis-server "$@"
fi

exec "$@"
