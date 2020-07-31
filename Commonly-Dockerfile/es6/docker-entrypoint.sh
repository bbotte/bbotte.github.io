#!/bin/bash
set -e

if [ "${MEMORY_LOCK}" == "true" ]; then
    ulimit -l unlimited
fi

if [ ! -d "/data/elasticsearch/data" ];then mkdir -p /data/elasticsearch/{data,logs} && chown -R elasticsearch.elasticsearch /data/elasticsearch/;fi

if [ ! -z "${ES_PLUGINS_INSTALL}" ]; then
    OLDIFS="${IFS}"
    IFS=","
    for plugin in ${ES_PLUGINS_INSTALL}; do
        if ! "${BASE}"/bin/elasticsearch-plugin list | grep -qs ${plugin}; then
            until "${BASE}"/bin/elasticsearch-plugin install --batch ${plugin}; do
                echo "Failed to install ${plugin}, retrying in 3s"
                sleep 3
            done
        fi
    done
    IFS="${OLDIFS}"
fi

if [ ! -z "$(env|grep KUBERNETES)" ];then
    POD_NAME=${POD_NAME}.${SERVICE_NAME}
fi

#rm -rf /elasticsearch/modules/x-pack/x-pack-ml
#rm -rf /elasticsearch/modules/x-pack-ml

export ES_JAVA_OPTS="-Des.cgroups.hierarchy.override=/ $ES_JAVA_OPTS"
if [ "$1" = 'elasticsearch' -a "$(id -u)" = '0' ]; then
    echo 222
    set -- "elasticsearch" "${@:2}"
    exec chroot --userspec=1000 / "${@}"
else
    exec "$@" $ES_EXTRA_ARGS
fi
