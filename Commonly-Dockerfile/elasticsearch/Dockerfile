FROM openjdk:8-jre-alpine

# ensure elasticsearch user exists
RUN addgroup -S elasticsearch && adduser -S -G elasticsearch elasticsearch

# grab su-exec for easy step-down from root
# and bash for "bin/elasticsearch" among others
RUN apk add --no-cache 'su-exec>=0.2' bash

RUN set -ex; \
	apk add --no-cache --virtual .fetch-deps \
	ca-certificates \
		gnupg \
		openssl \
		tar 
# wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.2.2.tar.gz
COPY elasticsearch-6.2.2.tar.gz /elasticsearch-6.2.2.tar.gz

WORKDIR /usr/share/elasticsearch
ENV PATH /usr/share/elasticsearch/bin:$PATH
ENV ELASTICSEARCH_PATH /usr/share/elasticsearch/bin

RUN set -ex; \
        dir="$(dirname "$ELASTICSEARCH_PATH")"; \
        \
        mkdir -p "$dir"; \
        tar -xf /elasticsearch-6.2.2.tar.gz --strip-components=1 -C "$dir"; \
        rm /elasticsearch-6.2.2.tar.gz; \
        \
	apk del .fetch-deps; \
	\
	mkdir -p ./plugins; \
	for path in \
		./data \
		./logs \
		./config \
		./config/scripts \
	; do \
		mkdir -p "$path"; \
		chown -R elasticsearch:elasticsearch "$path"; \
	done

ENV  NODE_NAME="" \
     ES_TMPDIR="/tmp"
#RUN  elasticsearch --version  # if your computer memory has above 1G 

COPY config/elasticsearch.yml /usr/share/elasticsearch/config/elasticsearch.yml

COPY docker-entrypoint.sh /
COPY Shanghai /etc/localtime
RUN apk add --no-cache curl
COPY curl.txt /

EXPOSE 9200 9300
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["elasticsearch"]
