---
layout: default
---

# flume-ng日志收集之安装配置

1. 环境说明
2. flume的安装
3. hadoop的配置
4. 新建hadoop存储的文件夹

### 环境说明

flume-ng日志收集之flume和hadoop的安装配置

```
                    kafka
logs ----> flume -----------> hadoop
```

在上一篇[logstash使用zookeeper建立kafka集群对日志收集](http://bbotte.com/logs-service/logstash-uses-zookeeper-to-establish-kafka-cluster-for-log-collection/)中有写zookeeper和kafka的安装配置，这里略过。通常的做法是flume采集日志，通过kafka这个消息队列传输给hadoop存储到硬盘落地。

```
[root@vm01 ~]# cat /etc/centos-release
CentOS release 6.7 (Final)
[root@vm01 ~]# cat /etc/hosts
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
10.211.55.4 vm01
[root@vm01 ~]# cat /etc/sysconfig/network
NETWORKING=yes
#HOSTNAME=localhost.localdomain
HOSTNAME=vm01
[root@vm01 ~]# hostname
vm01
```

### **flume的安装**

```
文档  http://flume.apache.org/FlumeUserGuide.html
wget http://apache.fayea.com/flume/1.6.0/apache-flume-1.6.0-bin.tar.gz
tar -xzf apache-flume-1.6.0-bin.tar.gz -C /usr/local/
ln -s /usr/local/apache-flume-1.6.0-bin/ /usr/local/flume
```

### **hadoop的配置**

```
文档  https://hadoop.apache.org/docs/r1.0.4/cn/index.html
http://apache.fayea.com/hadoop/common/hadoop-2.6.4/hadoop-2.6.4.tar.gz
tar -xzf hadoop-2.6.4.tar.gz -C /usr/local/
ln -s /usr/local/hadoop-2.6.4/ /usr/local/hadoop
 
# vim /root/.bashrc
export PATH=$PATH:/usr/local/flume/bin:/usr/local/kafka/bin/
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:/usr/local/hadoop/bin:/usr/local/hadoop/sbin
. /root/.bashrc
 
# cat /usr/local/hadoop/etc/hadoop/core-site.xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
        <property>
             <name>hadoop.tmp.dir</name>
             <value>file:/usr/local/hadoop/tmp/tmp</value>
             <description>Abase for other temporary directories.</description>
        </property>
        <property>
             <name>fs.defaultFS</name>
             <value>hdfs://vm01:9000</value>
        </property>
</configuration>
 
# cat /usr/local/hadoop/etc/hadoop/hdfs-site.xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
        <property>
             <name>dfs.replication</name>
             <value>1</value>
        </property>
        <property>
             <name>dfs.namenode.name.dir</name>
             <value>file:/usr/local/hadoop/tmp/name</value>
        </property>
        <property>
             <name>dfs.datanode.data.dir</name>
             <value>file:/usr/local/hadoop/tmp/data</value>
        </property>
</configuration>
```

配置文件设置好后就可以格式化设置的文件夹，上面配置文件中路径不用mkdir创建，当然线上不会把文件夹放到hadoop的安装目录，启动hadoop的服务

```
[root@vm01 ~]# hadoop namenode -format
DEPRECATED: Use of this script to execute hdfs command is deprecated.
Instead use the hdfs command for it.
 
16/08/11 01:17:55 INFO namenode.NameNode: STARTUP_MSG:
/************************************************************
STARTUP_MSG: Starting NameNode
STARTUP_MSG:   host = vm01/10.211.55.4
STARTUP_MSG:   args = [-format]
STARTUP_MSG:   version = 2.6.4
STARTUP_MSG:   classpath = /usr/local/hadoop-2.6.4/etc/hadoop:
...
...
16/08/11 01:17:56 INFO common.Storage: Storage directory /usr/local/hadoop/tmp/name has been successfully formatted.
16/08/11 01:17:56 INFO namenode.NNStorageRetentionManager: Going to retain 1 images with txid >= 0
16/08/11 01:17:56 INFO util.ExitUtil: Exiting with status 0
16/08/11 01:17:56 INFO namenode.NameNode: SHUTDOWN_MSG:
/************************************************************
SHUTDOWN_MSG: Shutting down NameNode at vm01/10.211.55.4
************************************************************/
```

我们只是用hdfs存储，所以不用start-all.sh，也木有用到调度，start-yarn.sh也不用启动，只需start-dfs.sh，如果有ssh登录提示，yes继续

```
[root@vm01 ~]# start-dfs.sh
16/08/11 01:21:34 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
Starting namenodes on [vm01]
vm01: starting namenode, logging to /usr/local/hadoop-2.6.4/logs/hadoop-root-namenode-vm01.out
localhost: starting datanode, logging to /usr/local/hadoop-2.6.4/logs/hadoop-root-datanode-vm01.out
Starting secondary namenodes [0.0.0.0]
0.0.0.0: starting secondarynamenode, logging to /usr/local/hadoop-2.6.4/logs/hadoop-root-secondarynamenode-vm01.out
16/08/11 01:21:49 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
```

### 新建hadoop存储的文件夹

```
# hadoop fs -mkdir -p /user/root/input
# hadoop jar /usr/local/hadoop-2.6.4/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.6.4.jar grep ./input ./output 'dfs[a-z.]+'
# hdfs dfs -ls /
# hdfs dfs -ls hdfs://vm01:9000/
# hadoop fs -ls /
# hadoop fs -ls hdfs://vm01:9000/
# hadoop fs -help         #更多命令看help
# hdfs dfsadmin -report
16/08/11 01:24:36 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
Configured Capacity: 52710469632 (49.09 GB)
Present Capacity: 36957294592 (34.42 GB)
DFS Remaining: 36957270016 (34.42 GB)
DFS Used: 24576 (24 KB)
DFS Used%: 0.00%
Under replicated blocks: 0
Blocks with corrupt replicas: 0
Missing blocks: 0
 
-------------------------------------------------
Live datanodes (1):
 
Name: 10.211.55.4:50010 (vm01)
Hostname: vm01
Decommission Status : Normal
Configured Capacity: 52710469632 (49.09 GB)
DFS Used: 24576 (24 KB)
Non DFS Used: 15753175040 (14.67 GB)
DFS Remaining: 36957270016 (34.42 GB)
DFS Used%: 0.00%
DFS Remaining%: 70.11%
Configured Cache Capacity: 0 (0 B)
Cache Used: 0 (0 B)
Cache Remaining: 0 (0 B)
Cache Used%: 100.00%
Cache Remaining%: 0.00%
Xceivers: 1
Last contact: Thu Aug 11 01:24:35 CST 2016
```

浏览器打开http://IP:50070/可以查看hadoop的状态等信息

2016年08月13日 于 [linux工匠](https://bbotte.github.io/) 发表


