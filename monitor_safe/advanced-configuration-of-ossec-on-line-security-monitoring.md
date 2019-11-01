# ossec线上安全监控的高级配置

1. 添加多个客户端
2. 远程管理客户端
3. 添加自定义log
4. 调整默认报警级别
5. 日志类别
6. 自动识别log
7. 同类的软件

### 说明

上一篇文章[ossec线上安全监控的配置详细文档](http://bbotte.com/monitor-safe/ossec%E7%BA%BF%E4%B8%8A%E5%AE%89%E5%85%A8%E7%9B%91%E6%8E%A7%E7%9A%84%E9%85%8D%E7%BD%AE%E8%AF%A6%E7%BB%86%E6%96%87%E6%A1%A3/) 写了ossec的安装应用、web界面，这一篇写ossec的高级用法，主要是批量部署管理

需要修改的参数
默认支持256个客户机，编译时候 make setmaxagents
修改系统参数 /etc/security/limits.conf 支持2048台主机

```
ossec soft nofile 2048
ossec hard nofile 2048
ossecr soft nofile 2048
ossecr hard nofile 2048
```

### **添加多个客户端**

```
yum -y install perl-Time-HiRes
注意：ossec解压目录下的ossec-batch-manager.pl
服务端执行：
./ossec-hids-2.8.1/contrib/ossec-batch-manager.pl -a -p 192.168.22.60 -n agent060
cat /var/ossec/etc/client.keys
001 agent060 192.168.22.60 12459b26ebc251551ef430c977fb9c6768c787a5dca18721cfde618775255652
scp /var/ossec/etc/client.keys root@192.168.22.60:/var/ossec/etc/
service ossec restart
 
客户机执行：
./ossec-hids-2.8.1/contrib/ossec-batch-manager.pl -e 192.168.22.60
service ossec restart
```

### **远程管理客户端**

```
# /usr/local/ossec/bin/agent_control -i 001        #查看客户端信息
OSSEC HIDS agent_control. Agent information:
   Agent ID:   001
   Agent Name: agent001
   IP address: 192.168.22.152
   Status:     Active
 
   Operating system:    Linux manager 2.6.32-431.el6.x86_64 #1 SMP Fri Nov 2..
   Client version:      OSSEC HIDS v2.8
   Last keep alive:     Fri Aug 14 11:49:08 2015
   Syscheck last started  at: Fri Aug 14 11:48:15 2015
   Rootcheck last started at: Fri Aug 14 10:39:16 2015
 
# /usr/local/ossec/bin/agent_control -R 001      #重启客户端
```

### **添加自定义log**

```
客户机执行：
./ossec-hids-2.8.1/contrib/util.sh addfile /var/log/nginx/nginx_access.log 
实际执行的操作为：
/var/ossec/etc/ossec.conf 配置文件追加如下：
    <ossec_config>
      <localfile>
      <log_format>syslog</log_format>
      <location>/var/log/nginx/nginx_access.log</location>
     </localfile>
   </ossec_config>
 
 
# vim /var/ossec/etc/ossec.conf
  <syscheck>
    <!-- Frequency that syscheck is executed - default to every 22 hours -->
    <frequency>79200</frequency>
 
    <alert_new_files>yes</alert_new_files>  #添加这一行
```

![ossec线上安全监控的高级配置-pic2](../images/2016/03/%E5%9B%BE%E7%89%875.png)

### **调整默认报警级别**

```
Received From: (agent060) 192.168.22.60->/var/log/nginx/nginx_access.log
Rule: 31151 fired (level 10) -> "Multiple web server 400 error codes from same source ip."
Portion of the log(s):
192.168.22.188 - - [15/Aug/2015:16:50:50 +0800] "GET /a.html HTTP/1.1" 404 564 "-" "Mozilla/5.0 \
(Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36" -
服务端：
/var/ossec/rules/web_rules.xml 
  <rule id="31151" level="10" frequency="12" timeframe="90">
 
创建新文件，rules的规则默认报警级别是0，可以修改为5
默认的报警级别设置：
rules/ossec_rules.xml
  <rule id="554" level="0">
在此配置添加：
rules/local_rules.xml
  <rule id="554" level="7" overwrite="yes">
    <category>ossec</category>
    <decoded_as>syscheck_new_entry</decoded_as>
    <description>File added to the system.</description>
    <group>syscheck,</group>
  </rule>
```

### **日志类别**

```
Default: syslog
Allowed:
 
syslog
This format is for plain text files in a syslog-like format. It can also be used when \
there is no support for the logging format, and the logs are single line messages.
 
snort-full
This is used for Snort’s full output format.
 
snort-fast
This is used for Snort’s fast output format.
 
squid         iis
 
eventlog
This is used for Microsoft Windows eventlog format.
 
eventchannel
This is used for Microsoft Windows eventlogs, using the new EventApi. This allows \
OSSEC to monitor both \
standard “Windows” eventlogs and more recent “Application and Services” logs. \
This support was added in 2.8.
 
mysql_log
This is used for MySQL logs. It does not support multi-line logs.
 
postgresql_log
This is used for PostgreSQL logs. It does not support multi-line logs.
 
nmapg
This is used for monitoring files conforming to the grepable output from nmap.
 
apache
This format is for apache’s default log format.
 
command
This format will be the output from the command (as run by root) defined by command. \
Each line of output will be treated as a separate log.
 
full_command
This format will be the output from the command (as run by root) defined by command. \
The entire output will be treated as a single log.
 
Warning：command and full_command cannot be used in the agent.conf, and must be \
configured in each system’s ossec.conf.
 
 
djb-multilog
 
multi-line：
 
This option will allow applications that log multiple lines per event to be monitored. \
This format requires the number of lines to be consistent. multi-line: is followed by \
the number of lines in each log entry. Each line will be combined with the previous \
lines until all lines are gathered. There may be multiple timestamps in a finalized event.
 
Allowed: <log_format>multi-line: NUMBER</log_format>
 
Example:
 
Log messages:
Aug  9 14:22:47 hostname log line one
Aug  9 14:22:47 hostname log line two
Aug  9 14:22:47 hostname log line three
Aug  9 14:22:47 hostname log line four
Aug  9 14:22:47 hostname log line five
 
Log message as analyzed by ossec-analysisd_:
 
Aug  9 14:22:47 hostname log line one Aug  9 14:22:47 hostname log line two Aug  9 14:22:47 hostname log line three Aug  9 14:22:47 hostname log line four Aug  9 14:22:47 hostname log line five
```

### **自动识别log**

php错误日志

```
grep -v ^\; /usr/local/php/etc/php.ini|sed '/^$/d'
error_reporting = E_ALL | E_STRICT
display_errors = On
display_startup_errors = On
log_errors = On
log_errors_max_len = 1024
ignore_repeated_errors = Off
ignore_repeated_source = Off
report_memleaks = On
track_errors = On
html_errors = On
error_log = /var/log/nginx/error.log
 
# grep access_log /usr/local/nginx/conf/server/phpcms.conf
        access_log  /var/log/nginx/access.log access;
 
# cat /var/www/www.test.com/phpinfo.php 
<?php
phpinfo();,              #这里多写个，
?>

```

安装ossec的时候会有如下提示：

```
3.5- Setting the configuration to analyze the following logs:
    -- /var/log/messages
    -- /var/log/secure
    -- /var/log/maillog
    -- /var/log/nginx/access.log (apache log)
    -- /var/log/nginx/error.log (apache log)
```

![ossec线上安全监控的高级配置-pic3](../images/2016/03/%E5%9B%BE%E7%89%876.png)

![ossec线上安全监控的高级配置-pic4](../images/2016/03/%E5%9B%BE%E7%89%877.png)

### **同类的软件**

http://www.tripwire.com/ 数据完整性校验
https://www.snort.org/ 嗅探器、数据包记录器、网络入侵检测系统
https://www.alienvault.com/products/ossim 包含nagios，ossec，snort，nessus
http://www.fail2ban.org/
http://denyhosts.sourceforge.net/

2016年03月15日 于 [linux工匠](http://www.bbotte.com/) 发表