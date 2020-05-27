---
layout: default
---

# ELK日志服务使用-rsyslog传输日志

在前两篇文章中，对elk的安装，运行，配置做了介绍。ELK中elasticsearch如果用单机，就不用配置什么，如果是集群，则需要3台或5台设置一下，因为说明文档解释的相当详细，这里不做多说明。kibana也没有多少需要设置的。下面我们主要说一下logstash的配置。
我们多数情况是多台web或者service服务器，均生成日志，由elk日志服务器处理，日志收集汇总又有多种方式，**下面几种方式在博客里面均有写**，大括号{}代表一台服务器，→代表传输方向，如果是“→redis→”代表通过redis通道传输日志：

```
#用rsyslog同步日志到elk服务器
{ rsyslog } →→ { rsyslog →→ logstash →→ elasticsearch →→ kibana } 
#logstash的shipper端发送，indexer端接收
{ logstash shipper } →→redis→→ { logstash indexer →→ elasticsearch →→ kibana } 
#使用rsyslog模块omhiredis传输日志
{ rsyslog } →→redis→→ { logstash →→ elasticsearch →→ kibana } 
#使用rsyslog模块omkafka传输日志
{ rsyslog } →→kafka→→ { logstash →→ elasticsearch →→ kibana }
```

下面说一下用rsyslog发送接收日志的配置过程，通过rsyslog把日志传输到另一台主机，存储为文件：

centos 6.6默认的rsyslog

```
# rsyslogd -v
rsyslogd 5.8.10, compiled with:
FEATURE_REGEXP: Yes
FEATURE_LARGEFILE: No
GSSAPI Kerberos 5 support: Yes
FEATURE_DEBUG (debug build, slow code): No
32bit Atomic operations supported: Yes
64bit Atomic operations supported: Yes
Runtime Instrumentation (slow code): No
rsyslog同步日志
```

### **发送日志端**：

在此添加日志的配置文件

```
/etc/rsyslog.d/dubbo.conf
$ModLoad imfile #if you want to tail file
$InputFileName /var/log/nginx/access.log
$InputFileTag server1_dubbo_log:
$InputFileStateFile state_server1_dubbo_log
$InputRunFileMonitor
$InputFilePollInterval 5
if $programname == 'server1_dubbo_log' then @192.168.71.46:1514
if $programname == 'server1_dubbo_log' then ~
```

### **接收日志端**：

```
# grep -v ^\# /etc/rsyslog.conf|sed '/^$/d'
$ModLoad imuxsock # provides support for local system logging (e.g. via logger command)
$ModLoad imklog # provides kernel logging support (previously done by rklogd)
$ModLoad imudp
$UDPServerRun 1514
$ActionFileDefaultTemplate RSYSLOG_TraditionalFileFormat
$IncludeConfig /etc/rsyslog.d/*.conf
*.info;mail.none;authpriv.none;cron.none;server*.none /var/log/messages
authpriv.* /var/log/secure
mail.* -/var/log/maillog
cron.* /var/log/cron
*.emerg *
uucp,news.crit /var/log/spooler
local7.* /var/log/boot.log
 
# vim /etc/rsyslog.d/dubbo.conf 
:rawmsg, contains, "server1_dubbo_log" /var/log/nginx/access.log
```

上述**配置说明**：
$InputFileTag定义的NAME必须唯一，同一台主机上不同的应用应当使用不同的NAME，否则会导致新定义的TAG不生效；
$InputFileStateFile定义的StateFile必须唯一，它被rsyslog用于记录文件上传进度，否则会导致混乱；
@192.168.71.46:1514用于指定接收日志的服务器，UDP协议，IP，port
有需要的话，$InputFileSeverity info 也添加上
$InputFilePollInterval 5 等待5秒钟发送一次,

上面那个图，接收日志端：/etc/rsyslog.conf 中
*.info;mail.none;authpriv.none;cron.none;server*.none /var/log/messages
之所以最后面加 server*.none，是因为发送日志端定义日志的tag，为 server1_dubbo_log，不加server*.none 就会在 /var/log/message 同时包存一份，占硬盘

配置完成后重启rsyslog服务

```
[root@localhost ~]# service rsyslog restart
Shutting down system logger: [ OK ]
Starting system logger: [ OK ]
```

测试：

**发送日志端**：

```
# echo "`date` this is test message" >> /var/log/nginx/access.log
```

**接收日志端**：

```
# tail -f /var/log/nginx/access.log
Feb 25 15:48:47 localhost server1_dubbo_log: Thu Feb 25 15:48:44 CST 2016 this is test message
```

rsyslog同步日志包含一个日志头，对于nginx来说的话无关紧要，elk直接分析这个日志就可以，另一种方法是rsyslog直接发送给另一台主机的某一个端口，发送端rsyslog的配置不变，如上配置，把日志通过tcp 1514端口发送给IP 192.168.71.46。接收端rsyslog不需要设置，因为用不到rsyslog来接收日志了，需要配置的是logstash。

由logstash接收，配置如下：

```
input {
syslog {
type => syslog
port => 1514
codec => plain { charset => "ISO-8859-1" }
}
}
 
filter {
mutate {
add_field => [ "hostip", "%{host}" ]
}
}
output {
elasticsearch {
host => "localhost"
}
}
```

启动elasticsearch和kibana，查看后台展示：

```
[root@localhost ~]# echo "`date` this is test message" >> /data/dubboService/nohup.out
[root@localhost ~]# tail -n 1 /data/dubboService/nohup.out
Thu Feb 25 16:30:51 CST 2016 this is test message
```

![ELK日志服务使用-rsyslog传输日志 - 第1张](../images/2016/02/QQ%E6%88%AA%E5%9B%BE20160225163209.png)

附nginx的配置，配置文件不用改动，例子：

```
# grep -v ^.*# /usr/local/nginx/conf/nginx.conf|sed '/^$/d'
worker_processes auto;
events {
worker_connections 10240;
}
http {
include mime.types;
default_type application/octet-stream;
log_format main '$remote_addr - $remote_user [$time_local] "$request" '
'$status $body_bytes_sent "$http_referer" '
'"$http_user_agent" "$http_x_forwarded_for"';
sendfile on;
keepalive_timeout 65;
server {
listen 80;
server_name localhost;
index index.html; #默认配置，修改了下面几行
root /var/www;
access_log /var/log/nginx/access.log main;
error_log /var/log/nginx/error.log;
error_page 500 502 503 504 /50x.html;
location = /50x.html {
root html;
}
}
}
```

nginx对应的logstash配置

```
input {
file {
    path => [ "/var/log/nginx/access.log" ]
    start_position => "beginning"
    type => "nginx"
}
}
 
filter {
  if [type] == "nginx" {
    grok {
      match => { "message" => "%{IPORHOST:clientip} - %{NOTSPACE:remote_user} \[%{HTTPDATE:timestamp}\] \"(?:%{WORD:method} %{NOTSPACE:request}(?: %{URIPROTO:proto}/%{NUMBER:httpversion})?|%{DATA:rawrequest})\" %{NUMBER:status} (?:%{NUMBER:upstime}|-) %{NUMBER:reqtime} (?:%{NUMBER:size}|-) %{QS:referrer} %{QS:agent} %{QS:xforwardedfor} %{QS:reqbody} %{WORD:scheme} (?:%{IPV4:upstream}(:%{POSINT:port})?|-)" }
      add_field => [ "received_at", "%{@timestamp}" ]
      add_field => [ "received_from", "%{host}" ]
    }
    date {
        match => [ "timestamp" , "dd/MMM/YYYY:HH:mm:ss Z" ]
    }
    }
}
 
output {
redis { host => "127.0.0.1" data_type => "list" key => "logstash:xxxx:access_log" }
}
```



2016年02月25日 于 [linux工匠](https://bbotte.github.io/) 发表