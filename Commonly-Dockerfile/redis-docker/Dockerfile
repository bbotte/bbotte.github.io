FROM alpine:3.7
RUN apk update && \
   apk add bash util-linux
# wget http://download.redis.io/releases/redis-4.0.1.tar.gz
COPY redis-4.0.1.tar.gz /redis-4.0.1.tar.gz
RUN set -ex; \
	apk add --no-cache --virtual .build-deps \
		coreutils \
		gcc \
		linux-headers \
		make \
		musl-dev ; \
        tar -xzf /redis-4.0.1.tar.gz -C /tmp ; \
        mv /tmp/redis-4.0.1 /tmp/redis ; \
        rm -f /redis-4.0.1.tar.gz ; \
\
# disable Redis protected mode [1] as it is unnecessary in context of Docker
# (ports are not automatically exposed when running inside Docker, but rather explicitly by specifying -p / -P)
# [1]: https://github.com/antirez/redis/commit/edd4d555df57dc84265fdfb4ef59a4678832f6da
        grep -q '^#define CONFIG_DEFAULT_PROTECTED_MODE 1$' /tmp/redis/src/server.h; \
        sed -ri 's!^(#define CONFIG_DEFAULT_PROTECTED_MODE) 1$!\1 0!' /tmp/redis/src/server.h; \
        grep -q '^#define CONFIG_DEFAULT_PROTECTED_MODE 0$' /tmp/redis/src/server.h ;\
\
        make -C /tmp/redis distclean ; \
        make -C /tmp/redis -j "$(nproc)"; \
        make -C /tmp/redis install; \
        \
        rm -r /tmp/redis; \
        runDeps="$( \
		scanelf --needed --nobanner --format '%n#p' --recursive /usr/local \
			| tr ',' '\n' \
			| sort -u \
			| awk 'system("[ -e /usr/local/lib/" $1 " ]") == 0 { next } { print "so:" $1 }' \
	)"; \
	apk add --virtual .redis-rundeps $runDeps; \
	apk del .build-deps; \
        redis-server --version

COPY redis.conf /etc/redis.conf
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
WORKDIR /

ENTRYPOINT ["/docker-entrypoint.sh"]

EXPOSE 6379
CMD [ "redis-server","/etc/redis.conf" ]
