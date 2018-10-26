FROM openjdk:8-jre-alpine

# ensure logstash user exists
RUN addgroup -S logstash && adduser -S -G logstash logstash

# install plugin dependencies
RUN apk add --no-cache \
# env: can't execute 'bash': No such file or directory
		bash \
		libc6-compat \
		libzmq

# grab su-exec for easy step-down from root
RUN apk add --no-cache 'su-exec>=0.2'

# https://www.elastic.co/guide/en/logstash/5.0/installing-logstash.html#_apt
# https://artifacts.elastic.co/GPG-KEY-elasticsearch

ENV LOGSTASH_PATH /usr/share/logstash/bin
ENV PATH $LOGSTASH_PATH:$PATH
# wget https://artifacts.elastic.co/downloads/logstash/logstash-6.2.2.tar.gz
COPY logstash-6.2.2.tar.gz /logstash.tar.gz && \
	apk add --no-cache --virtual .fetch-deps \
		ca-certificates \
		gnupg \
		openssl \
		tar \
	; \
	\
	dir="$(dirname "$LOGSTASH_PATH")"; \
	\
	mkdir -p "$dir"; \
	tar -xf /logstash.tar.gz --strip-components=1 -C "$dir"; \
	rm /logstash.tar.gz; \
	\
	apk del .fetch-deps; \
	\
	export LS_SETTINGS_DIR="$dir/config"; \
# if the "log4j2.properties" file exists (logstash 5.x), let's empty it out so we get the default: "logging only errors to the console"
	if [ -f "$LS_SETTINGS_DIR/log4j2.properties" ]; then \
		cp "$LS_SETTINGS_DIR/log4j2.properties" "$LS_SETTINGS_DIR/log4j2.properties.dist"; \
		truncate -s 0 "$LS_SETTINGS_DIR/log4j2.properties"; \
	fi; \
	\
# set up some file permissions
	for userDir in \
		"$dir/config" \
		"$dir/data" \
	; do \
		if [ -d "$userDir" ]; then \
			chown -R logstash:logstash "$userDir"; \
		fi; \
	done; \
	\
	logstash --version
COPY Shanghai /etc/localtime 

COPY docker-entrypoint.sh /
COPY logstash-shipper.conf /
RUN chmod +x /docker-entrypoint.sh
WORKDIR /

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["-f", "/logstash-shipper.conf"]
