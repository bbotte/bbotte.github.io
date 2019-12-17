---
layout: default
---

# ELK5完整部署

1. 结构图
2. 版本说明
3. 系统环境
4. zookeeper配置
5. 公网kafka配置
6. elasticsearch配置
7. kibana配置
8. nginx配置
9. logstash配置
10. 服务启动及关闭

ELK5完整部署，日志由logstash shipper收集，并传输给kafka，再有logstash indexer从kafka获取日志，解析后发送到elasticsearch数据库，kibana图形化界面展示

### **结构图**

```
------------------      ----------      -----------------      -----------------      _______
app-server生成log  |    |          |    |                 |    |                 |    |       |
                  |----|kafka     |----|logstash indexer |----|elasticsearch db |----|kibana |
logstash shipper  |    |          |    |                 |    |                 |    |       |
------------------     -----------      -----------------     ------------------     |_______|
```

### **版本说明**

```
CentOS Linux release 7.3.1611 (Core)
zookeeper-3.4.10.tar.gz
kafka_2.11-0.11.0.1.tgz 
jdk-8u66-linux-x64.rpm 
logstash-5.4.1.rpm 
kibana-5.4.1-x86_64.rpm
elasticsearch-5.4.1.rpm
```

解压压缩包，创建目录等操作忽略

### **系统环境**

```
sed -i 's/\#Port\ 22/Port 8888/' /etc/ssh/sshd_config
systemctl reload sshd
rm -f /etc/localtime
ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
setenforce 0
cat >> /etc/security/limits.conf << EOF
* soft nproc 65535
* hard nproc 65535
* soft nofile 65535
* hard nofile 65535
EOF
sed -i 's/4096/10240/' /etc/security/limits.d/20-nproc.conf
echo "ulimit -SHn 65535" >> /etc/profile
. /etc/profile
ntpdate ntp1.aliyun.com
yum install -y python-devel vim glibc wget lrzsz bc ntpdate
rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
```

由于环境特殊，需要zookeeper和kafka对外，所以下面是数据走公网的配置

### **zookeeper配置**

```
# egrep -v "^#|^$" /usr/local/zookeeper/conf/zoo.cfg 
tickTime=2000
initLimit=10
syncLimit=5
dataDir=/data/zk/data
clientPort=2181
server.1=139.219.X.X:2888:3888
 
# echo 1 > /data/zk/data/myid
```

内网单机zookeeper配置

```
/usr/local/zookeeper/conf/zoo.cfg 
tickTime=2000
initLimit=10
syncLimit=5
dataDir=/usr/local/zookeeper/data
clientPort=2181
maxClientCnxns=120
```

### **公网kafka配置**

```
# egrep -v "^#|^$" /usr/local/kafka/config/server.properties 
broker.id=0
listeners=PLAINTEXT://:9092
num.network.threads=3
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600
log.dirs=/data/kafka
num.partitions=3
num.recovery.threads.per.data.dir=1
log.retention.hours=168
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000
zookeeper.connect=139.219.X.X:2181
zookeeper.connection.timeout.ms=10000
delete.topic.enable=true
host.name=139.219.X.X
advertised.host.name=139.219.X.X
auto.create.topics.enable=true
offsets.topic.replication.factor=1
 
# egrep -v "^#|^$" /usr/local/kafka/config/producer.properties 
bootstrap.servers=139.219.X.X:9092
compression.type=none
 
# vim /etc/profile
export PATH=/usr/local/zookeeper/bin:$PATH
export PATH=/usr/local/kafka/bin:$PATH
# . /etc/profile
```

内网单机kafka配置

```
/usr/local/kafka/config/server.properties
broker.id=0
listeners=PLAINTEXT://10.11.11.14:9092
num.network.threads=3
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600
log.dirs=/usr/local/kafka/kafka-data
num.partitions=2
num.recovery.threads.per.data.dir=1
offsets.topic.replication.factor=1
transaction.state.log.replication.factor=1
transaction.state.log.min.isr=1
log.retention.hours=168
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000
zookeeper.connect=localhost:2181
zookeeper.connection.timeout.ms=6000
group.initial.rebalance.delay.ms=0
delete.topic.enable=true
host.name=10.11.11.14
auto.create.topics.enable=true
```

### **elasticsearch配置**

```
# egrep -v "^#|^$" /etc/elasticsearch/elasticsearch.yml 
path.data: /data/es/db
path.logs: /data/es/logs
network.host: 172.16.1.1
http.port: 9200
http.cors.enabled: true
http.cors.allow-origin: "*"
```

### **kibana配置**

```
# egrep -v "^#|^$" /etc/kibana/kibana.yml 
server.port: 5601
server.host: "10.11.11.14"
server.basePath: "/kibana"
elasticsearch.url: "http://172.16.1.1:9200"
kibana.index: ".kibana"
```

### **nginx配置**

```
# cat /etc/yum.repos.d/nginx.repo 
[nginx]
name=nginx repo
baseurl=http://nginx.org/packages/centos/7/$basearch/
gpgcheck=0
enabled=1
# yum install -y nginx
# egrep -v "^#|^$|.*#" /etc/nginx/conf.d/default.conf 
server {
    listen       80;
    server_name  www.bbotte.com;
    access_log  /var/log/nginx/host.access.log  main;
    location  / {
        proxy_pass   http://127.0.0.1:80;
    }
    location ~ ^/kibana/(.*)$ {
      auth_basic "Access Denied";
      auth_basic_user_file /etc/nginx/conf.d/pswd;
      rewrite /kibana/(.*)$ /$1 break;
      proxy_pass http://10.11.11.14:5601;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection 'upgrade';
      proxy_set_header Host $host;
      proxy_cache_bypass $http_upgrade;
      allow 117.143.77.1;
      deny all;
    }
    location /grafana {
        proxy_pass http://10.11.11.14:3000;
        rewrite  ^/grafana/(.*) /$1 break;
        allow 117.143.77.1;
        deny all;
    }
}
```

### **logstash配置**

logstash分2块，收集主机日志的logstash-shipper，和汇总日志的logstash-indexer
例如，日志格式为：
a.log格式

```
172.16.1.1 - - [11/Oct/2017:00:00:00 +0800] "GET /info HTTP/1.1" 200 12 1
```

b.log格式

```
2017-08-24 00:00:08.425 [DiscoveryClient-HeartbeatExecutor-0] [ERROR] The registered message body readers compatible with the MIME media type are:
    com.sun.jersey.core.impl.provider.entity.FormProvider
```

配置如下：

logstash-shipper.conf

```
/etc/logstash/conf.d/logstash-shipper.conf
input {
    file {
        path => [ "/path/for/logs/*/a.log"]
            codec => plain { format => "%{message}" }
            type => "access_log"
            sincedb_path => "/data/sincedb/access_log"
        }
    file {
        path => [ "/path/for/logs/*/b.log"]
            type => "java_log"
            sincedb_path => "/data/sincedb/java_log"
        codec => multiline {
            pattern => "^\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d.\d\d\d\ .+"
            negate => true
            what => "previous"
            max_lines => 200
            }
        }
}
output {
    if [type] == 'access_log' {
        kafka {
                bootstrap_servers => "139.219.X.X:9092"
                topic_id => "access_log"
            }
    }
    if [type] == 'java_log' {
        kafka {
                bootstrap_servers => "139.219.X.X:9092"
                topic_id => "java_log"
            }
    }
}
```

logstash-indexer.conf

```
/etc/logstash/conf.d/logstash-indexer.conf
input {
    kafka {
            bootstrap_servers => "139.219.X.X:9092"
            topics => "access_log"
            type => "access_log"
    }
    kafka {
            bootstrap_servers => "139.219.X.X:9092"
            topics => "java_log"
            type => "java_log"
    }
}
filter {
    if [type] == 'access_log' {
        if "_grokparsefailure" in [tags] {
              drop { }
          }
        grok {
                match => {
                    "message" => '%{IP} - - \[%{HTTPDATE:time}\] "%{WORD:methord} %{URIPATHPAR
AM:request} HTTP/%{NUMBER:httpversion}" %{NUMBER:response} %{GREEDYDATA}'
                    }
            }
        date {
            match => ["time","dd/MMM/yyyy:HH:mm:ss +\d+"]
            locale => "cn"
        }
    }
	if [type] != 'access_log' {
        if "_grokparsefailure" in [tags] {
              drop { }
          }
        grok {
            match => {
                ""message" => "%{TIMESTAMP_ISO8601:timestamp} \[%{WORD:exp}.%{WORD:jv}:%{NUMBER:\d+}\] %{LOGLEVEL:severity} %{GREEDYDATA:message}"}"
            }
        }
        date {
            match => ["timestamp","yyyy-MM-dd HH:mm:ss.SSS"]
            locale => "cn"
        }
    }
}
output {
    if [type] == 'access_log' {
        elasticsearch {
            hosts => "172.16.1.1:9200"
            index => "bbotte-nginx-access_log-%{+YYYY.MM.dd}"
        }
    }
    if [type] == 'java_log' {
        elasticsearch {
            hosts => "172.16.1.1:9200"
            index => "bbotte-nginx-java_log-%{+YYYY.MM.dd}"
        }
    }
}
```

### **服务启动及关闭**

```
zookeeper:
zkServer.sh start/stop
kafka: 
kafka-server-start.sh -daemon /usr/local/kafka/config/server.properties 
kafka-server-stop.sh
logstash:
systemctl start/stop logstash
elasticsearch:
/etc/init.d/elasticsearch start/stop
kibana:
/etc/init.d/kibana start/stop
nginx:
nginx
ps aux|grep [n]ginx|awk '{print $2}'|xargs kill
```

遇到的问题：

```
[INFO ][org.apache.kafka.common.utils.AppInfoParser] Kafka version : 1.0.0
[2018-08-31T17:07:24,896][INFO ][org.apache.kafka.common.utils.AppInfoParser] Kafka commitId : aaa7af6d4a11b29d
[2018-08-31T17:07:24,896][WARN ][org.apache.kafka.common.utils.AppInfoParser] Error registering AppInfo mbean
javax.management.InstanceAlreadyExistsException: kafka.consumer:type=app-info,id=logstash-0
        at com.sun.jmx.mbeanserver.Repository.addMBean(Repository.java:437) ~[?:1.8.0_161]
        at com.sun.jmx.interceptor.DefaultMBeanServerInterceptor.registerWithRepository(DefaultMBeanServerInterceptor.java:1898) ~[?:1.8.0_161]
        at com.sun.jmx.interceptor.DefaultMBeanServerInterceptor.registerDynamicMBean(DefaultMBeanServerInterceptor.java:966) ~[?:1.8.0_161]
        at com.sun.jmx.interceptor.DefaultMBeanServerInterceptor.registerObject(DefaultMBeanServerInterceptor.java:900) ~[?:1.8.0_161]
        at com.sun.jmx.interceptor.DefaultMBeanServerInterceptor.registerMBean(DefaultMBeanServerInterceptor.java:324) ~[?:1.8.0_161]
        at com.sun.jmx.mbeanserver.JmxMBeanServer.registerMBean(JmxMBeanServer.java:522) ~[?:1.8.0_161]
        at org.apache.kafka.common.utils.AppInfoParser.registerAppInfo(AppInfoParser.java:62) [kafka-clients-1.0.0.jar:?]
        at org.apache.kafka.clients.consumer.KafkaConsumer.<init>(KafkaConsumer.java:773) [kafka-clients-1.0.0.jar:?]
        at org.apache.kafka.clients.consumer.KafkaConsumer.<init>(KafkaConsumer.java:635) [kafka-clients-1.0.0.jar:?]
        at org.apache.kafka.clients.consumer.KafkaConsumer.<init>(KafkaConsumer.java:617) [kafka-clients-1.0.0.jar:?]
        at sun.reflect.NativeConstructorAccessorImpl.newInstance0(Native Method) [?:1.8.0_161]
        at sun.reflect.NativeConstructorAccessorImpl.newInstance(NativeConstructorAccessorImpl.java:62) [?:1.8.0_161]
        at sun.reflect.DelegatingConstructorAccessorImpl.newInstance(DelegatingConstructorAccessorImpl.java:45) [?:1.8.0_161]
        at java.lang.reflect.Constructor.newInstance(Constructor.java:423) [?:1.8.0_161]
...
[INFO ][org.apache.kafka.clients.consumer.internals.AbstractCoordinator] [Consumer clientId=logstash-0, groupId=logstash] (Re-)joining group
[INFO ][org.apache.kafka.clients.consumer.internals.ConsumerCoordinator] [Consumer clientId=logstash-0, groupId=logstash] Setting newly assigned partitions [testlog-1, testlog-0]
[INFO ][logstash.outputs.kafka   ] Sending batch to Kafka failed. Will retry after a delay. {:batch_size=>1, :failures=>1, :sleep=>0.1}
```

logstash的indexer.conf和shipper.conf配置同时在/etc/logstash/conf.d/ ,同时启动会有上述提示，分开执行即可



2017年10月13日 于 [linux工匠](http://www.bbotte.com/) 发表