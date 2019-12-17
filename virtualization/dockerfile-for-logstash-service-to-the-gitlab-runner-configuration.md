---
layout: default
---

# CICD之logstash服务的Dockerfile使用Gitlab Runner打docker包

gitlab提交代码后，经gitlab Runner打docker包，推送到docker仓库，然后kubernetes选择版本更新

**Dockerfile**

```
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
 
# LOGSTASH_TARBALL="https://artifacts.elastic.co/downloads/logstash/logstash-5.5.0.tar.gz"
 
COPY logstash-5.5.0.tar.gz /logstash.tar.gz
RUN set -ex; \
	apk add --no-cache --virtual .fetch-deps \
		ca-certificates \
		gnupg \
		openssl \
		tar ; \
	dir="$(dirname "$LOGSTASH_PATH")"; \
	mkdir -p "$dir"; \
	tar -xf /logstash.tar.gz --strip-components=1 -C "$dir"; \
	rm logstash.tar.gz; \
	apk del .fetch-deps; \
	export LS_SETTINGS_DIR="$dir/config"; \
# if the "log4j2.properties" file exists (logstash 5.x), let's empty it out so we get the default: "logging only errors to the console"
	if [ -f "$LS_SETTINGS_DIR/log4j2.properties" ]; then \
		cp "$LS_SETTINGS_DIR/log4j2.properties" "$LS_SETTINGS_DIR/log4j2.properties.dist"; \
		truncate -s 0 "$LS_SETTINGS_DIR/log4j2.properties"; \
	fi; \
# set up some file permissions
	for userDir in \
		"$dir/config" \
		"$dir/data" \
	; do \
		if [ -d "$userDir" ]; then \
			chown -R logstash:logstash "$userDir"; \
		fi; \
	done; \
	logstash --version
 
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
COPY logstash-shipper.conf /
RUN mkdir -p /data/logs/sincedb
RUN chown logstash.logstash -R /data/logs/sincedb
WORKDIR /
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["-f", "/logstash-shipper.conf"]
```

**docker-entrypoint.sh**

```
#!/bin/bash
set -e
mkdir -p /data/logs/sincedb
chown logstash.logstash -R /data/logs/sincedb
 
# first arg is `-f` or `--some-option`
if [ "${1#-}" != "$1" ]; then
	set -- logstash "$@"
fi
 
# Run as user "logstash" if the command is "logstash"
# allow the container to be started with `--user`
if [ "$1" = 'logstash' -a "$(id -u)" = '0' ]; then
	set -- su-exec logstash "$@"
fi
 
exec "$@"
```

logstash-5.5.0.tar.gz 从官方下载 <https://www.elastic.co/cn/downloads/logstash>

**logstash-shipper.conf样例**

```
input {
    file {
	    path => [ "/data/logs/service/*/*.log"]
		type => "service"
		sincedb_path => "/data/logs/sincedb/service"
        codec => multiline {
            pattern => "^\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d.\d\d\d .+"
            negate => true
            what => "previous"
            max_lines => 30
        }		
	}
    file {
	    path => [ "/data/logs/web/*/access_log*.log"]
	        codec => plain { format => "%{message}" }
		type => "web"
		sincedb_path => "/data/logs/sincedb/web"
	}
}
output {
    if [type] == 'service' {
        kafka {
	        codec => plain { format => "%{message}" }
	        bootstrap_servers => "139.219.*.*:9092"
		topic_id => "service"
	    }
    }
	if [type] == 'web' {
        kafka {
                codec => plain { format => "%{message}" }
	        bootstrap_servers => "139.219.*.*:9092"
		topic_id => "web"
	    }
    }
}
```

service的日志开头是2017-12-01 12:01:01，所以pattern匹配时间，根据时间判断日志的起始点；web日志原封不动传过去，output到kafka集群，logstash-indexer从kafka获取日志后归入elasticsearch

logstash-indexer.conf示例

```
input {
        kafka {
                bootstrap_servers => "139.219.*.*:9092"
                topics => "service"
                type => "service"
        }
        kafka {
                bootstrap_servers =>"139.219.*.*:9092"
                topics => "web"
                type => "web"
        }
}
filter {
    if [type] != ['web'] {
        if "_grokparsefailure" in [tags] {
              drop { }
          }
        grok {
            match => {
                "message" => "%{TIMESTAMP_ISO8601:timestamp} %{GREEDYDATA}"
            }
        }
        date {
            match => ["timestamp","yyyy-MM-dd HH:mm:ss.SSS"]
            locale => "cn"
        }
    }
    if [type] == 'web' {
        if "_grokparsefailure" in [tags] {
              drop { }
          }
        grok {
                match => {
                    "message" => '%{IP} - - \[%{HTTPDATE:time}\] "%{WORD:methord} %{URIPATHPARAM:request} HTTP/%
{NUMBER:httpversion}" %{NUMBER:response} %{GREEDYDATA}'
                    }
            }
        date {
            match => ["time","dd/MMM/yyyy:HH:mm:ss +\d+"]
            locale => "cn"
        }
    }
}
output {
        if [type] == 'service' {
                elasticsearch {
                        hosts => "172.16.1.1:9200"
                        index => "bbotte-service-%{+YYYY.MM.dd}"
                }
        }
        if [type] == 'web' {
                elasticsearch {
                        hosts => "172.16.1.1:9200"
                        index => "bbotte-web-%{+YYYY.MM.dd}"
                }
        }
}
```

最后就是**gitlabci配置**示例

```
# cat .gitlab-ci.yml
image: docker:latest
 
stages:
  - LogstashPubTest
  - LogstashPubProd
 
image-build-test:
  stage: LogstashPubTest
  script:
    - "current_date=`TZ='UTC-8' date +'%m%d%H%M'`"
    - "commit_sha=$CI_COMMIT_SHA"
    - "docker build -t bbotte.com:5000/logstash:$CI_COMMIT_REF_NAME-$current_date-${commit_sha:0:8} ."
    - "docker login -u admin -p 123456 bbotte.com:5000"
    - "docker push bbotte.com:5000/logstash:$CI_COMMIT_REF_NAME-$current_date-${commit_sha:0:8}"
  only:
    - test
image-build-master:
  stage: LogstashPubProd
  script:
    - "current_date=`TZ='UTC-8' date +'%m%d%H%M'`"
    - "commit_sha=$CI_COMMIT_SHA"
    - "docker build -t bbotte.com:5000/logstash:$CI_COMMIT_REF_NAME-$current_date-${commit_sha:0:8} ."
    - "docker login -u admin -p 123456 bbotte.com:5000"
    - "docker push bbotte.com:5000/logstash:$CI_COMMIT_REF_NAME-$current_date-${commit_sha:0:8}"
  only:
    - master
```

目录结构如下：

```
logstash$ ls -a
.   docker-entrypoint.sh  .git            logstash-5.5.0.tar.gz 
..  Dockerfile            .gitlab-ci.yml  logstash-shipper.conf
```

2018年01月08日 于 [linux工匠](http://www.bbotte.com/) 发表