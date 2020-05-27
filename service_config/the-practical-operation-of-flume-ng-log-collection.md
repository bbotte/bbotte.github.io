---
layout: default
---

# flume-ng日志收集之实践操作

1. kafka创建一个topic
2. 启动hadoop的dfs
3. 编辑flume的配置文件并运行
4. flume配置
5. 在hdfs查看内容
6. 使用kafka的flume配置
7. flume读取日志文件存储到hdfs

### **kafka创建一个topic**

名字暂定log2

```
# /usr/local/kafka/bin/kafka-topics.sh --create --zookeeper localhost --partitions 3 --replication-factor 2 --topic log2
# kafka-topics.sh --describe --zookeeper localhost:2181 --topic log2
Topic:log2     	PartitionCount:3       	ReplicationFactor:2    	Configs:
       	Topic: log2    	Partition: 0   	Leader: 1      	Replicas: 1,0  	Isr: 0,1
       	Topic: log2    	Partition: 1   	Leader: 2      	Replicas: 2,1  	Isr: 1,2
       	Topic: log2    	Partition: 2   	Leader: 0      	Replicas: 0,2  	Isr: 0,2
```

### **启动hadoop的dfs**

```
# start-dfs.sh
# hadoop fs -mkdir /log2
# hadoop fs -ls /
```

### **编辑flume的配置文件并运行**

**![flume-ng日志收集之实践操作 - 第1张](http://flume.apache.org/_images/DevGuide_image00.png)**

### flume配置

下面配置文件为**flume收集logs发送给hdfs：**

```
# mkdir -p /tmp/testlog/{data,log,point}
# cat /usr/local/flume/conf/logspool.properties
#agent1 name
agent1.sources=source1
agent1.sinks=sink1
agent1.channels=channel1
 
#Spooling Directory
#set source1
agent1.sources.source1.type=spooldir
agent1.sources.source1.spoolDir=/tmp/testlog/data
agent1.sources.source1.channels=channel1
agent1.sources.source1.fileHeader = false
agent1.sources.source1.interceptors.i1.type = timestamp
 
#set sink1
agent1.sinks.sink1.type=hdfs
agent1.sinks.sink1.hdfs.path=hdfs://vm01:9000/log2
agent1.sinks.sink1.hdfs.fileType=DataStream
agent1.sinks.sink1.hdfs.writeFormat=TEXT
agent1.sinks.sink1.hdfs.rollInterval=1
agent1.sinks.sink1.channel=channel1
#agent1.sinks.sink1.hdfs.filePrefix=%Y-%m-%d
 
#set channel1
agent1.channels.channel1.type=file
agent1.channels.channel1.checkpointDir=/tmp/testlog/point/
agent1.channels.channel1.dataDirs=/tmp/testlog/log/
```

flume执行上面配置，并向flume source文件写日志

```
# cd /usr/local/flume/
# flume-ng agent -n agent1 -c conf -f conf/logspool.properties -Dflume.root.logger=DEBUG,console
...
SOURCES: {source1={ parameters:{fileHeader=false, interceptors.i1.type=timestamp, channels=channel1, spoolDir=/tmp/testlog/data, type=spooldir} }}
CHANNELS: {channel1={ parameters:{checkpointDir=/tmp/testlog/point/, dataDirs=/tmp/testlog/log/, type=file} }}
SINKS: {sink1={ parameters:{hdfs.fileType=DataStream, hdfs.path=hdfs://vm01:9000/log2, hdfs.rollInterval=1, hdfs.writeFormat=TEXT, type=hdfs, channel=channel1} }}
...
2016-08-15 15:35:45,583 (conf-file-poller-0) [INFO - org.apache.flume.conf.FlumeConfiguration.validateConfiguration(FlumeConfiguration.java:141)] Post-validation flume configuration contains configuration for agents: [agent1]
2016-08-15 15:35:45,583 (conf-file-poller-0) [INFO - org.apache.flume.node.AbstractConfigurationProvider.loadChannels(AbstractConfigurationProvider.java:145)] Creating channels
2016-08-15 15:35:45,591 (conf-file-poller-0) [INFO - org.apache.flume.channel.DefaultChannelFactory.create(DefaultChannelFactory.java:42)] Creating instance of channel channel1 type file
2016-08-15 15:35:45,611 (conf-file-poller-0) [INFO - org.apache.flume.node.AbstractConfigurationProvider.loadChannels(AbstractConfigurationProvider.java:200)] Created channel channel1
2016-08-15 15:35:45,611 (conf-file-poller-0) [INFO - org.apache.flume.source.DefaultSourceFactory.create(DefaultSourceFactory.java:41)] Creating instance of source source1, type spooldir
2016-08-15 15:35:45,620 (conf-file-poller-0) [INFO - org.apache.flume.sink.DefaultSinkFactory.create(DefaultSinkFactory.java:42)] Creating instance of sink: sink1, type: hdfs
2016-08-15 15:35:45,630 (conf-file-poller-0) [INFO - org.apache.flume.node.AbstractConfigurationProvider.getConfiguration(AbstractConfigurationProvider.java:114)] Channel channel1 connected to [source1, sink1]
2016-08-15 15:35:45,637 (conf-file-poller-0) [INFO - org.apache.flume.node.Application.startAllComponents(Application.java:138)] Starting new configuration:{ sourceRunners:{source1=EventDrivenSourceRunner: { source:Spool Directory source source1: { spoolDir: /tmp/testlog/data } }} sinkRunners:{sink1=SinkRunner: { policy:org.apache.flume.sink.DefaultSinkProcessor@7c2d0928 counterGroup:{ name:null counters:{} } }} channels:{channel1=FileChannel channel1 { dataDirs: [/tmp/testlog/log] }} }
2016-08-15 15:35:45,646 (conf-file-poller-0) [INFO - org.apache.flume.node.Application.startAllComponents(Application.java:145)] Starting Channel channel1
...
2016-08-15 15:35:45,837 (lifecycleSupervisor-1-0) [INFO - org.apache.flume.channel.file.FileChannel.start(FileChannel.java:301)] Queue Size after replay: 0 [channel=channel1]
2016-08-15 15:35:45,838 (lifecycleSupervisor-1-0) [INFO - org.apache.flume.instrumentation.MonitoredCounterGroup.register(MonitoredCounterGroup.java:120)] Monitored counter group for type: CHANNEL, name: channel1: Successfully registered new MBean.
2016-08-15 15:35:45,838 (lifecycleSupervisor-1-0) [INFO - org.apache.flume.instrumentation.MonitoredCounterGroup.start(MonitoredCounterGroup.java:96)] Component type: CHANNEL, name: channel1 started
2016-08-15 15:35:45,838 (conf-file-poller-0) [INFO - org.apache.flume.node.Application.startAllComponents(Application.java:173)] Starting Sink sink1
2016-08-15 15:35:45,840 (conf-file-poller-0) [INFO - org.apache.flume.node.Application.startAllComponents(Application.java:184)] Starting Source source1
2016-08-15 15:35:45,840 (lifecycleSupervisor-1-4) [INFO - org.apache.flume.source.SpoolDirectorySource.start(SpoolDirectorySource.java:78)] SpoolDirectorySource source starting with directory: /tmp/testlog/data
2016-08-15 15:35:45,841 (lifecycleSupervisor-1-2) [INFO - org.apache.flume.instrumentation.MonitoredCounterGroup.register(MonitoredCounterGroup.java:120)] Monitored counter group for type: SINK, name: sink1: Successfully registered new MBean.
2016-08-15 15:35:45,841 (lifecycleSupervisor-1-2) [INFO - org.apache.flume.instrumentation.MonitoredCounterGroup.start(MonitoredCounterGroup.java:96)] Component type: SINK, name: sink1 started
2016-08-15 15:35:45,854 (lifecycleSupervisor-1-4) [INFO - org.apache.flume.instrumentation.MonitoredCounterGroup.register(MonitoredCounterGroup.java:120)] Monitored counter group for type: SOURCE, name: source1: Successfully registered new MBean.
2016-08-15 15:35:45,854 (lifecycleSupervisor-1-4) [INFO - org.apache.flume.instrumentation.MonitoredCounterGroup.start(MonitoredCounterGroup.java:96)] Component type: SOURCE, name: source1 started
...
2016-08-15 15:42:37,196 (pool-6-thread-1) [INFO - org.apache.flume.client.avro.ReliableSpoolingFileEventReader.readEvents(ReliableSpoolingFileEventReader.java:258)] Last read took us just up to a file boundary. Rolling to the next file, if there is one.
2016-08-15 15:42:37,196 (pool-6-thread-1) [INFO - org.apache.flume.client.avro.ReliableSpoolingFileEventReader.rollCurrentFile(ReliableSpoolingFileEventReader.java:348)] Preparing to move file /tmp/testlog/data/1.log to /tmp/testlog/data/1.log.COMPLETED
2016-08-15 15:42:41,115 (SinkRunner-PollingRunner-DefaultSinkProcessor) [INFO - org.apache.flume.sink.hdfs.BucketWriter.open(BucketWriter.java:234)] Creating hdfs://vm01:9000/log2/FlumeData.1471246960903.tmp
2016-08-15 15:42:43,300 (hdfs-sink1-roll-timer-0) [INFO - org.apache.flume.sink.hdfs.BucketWriter.close(BucketWriter.java:363)] Closing hdfs://vm01:9000/log2/FlumeData.1471246960903.tmp
2016-08-15 15:42:43,323 (hdfs-sink1-call-runner-4) [INFO - org.apache.flume.sink.hdfs.BucketWriter$8.call(BucketWriter.java:629)] Renaming hdfs://vm01:9000/log2/FlumeData.1471246960903.tmp to hdfs://vm01:9000/log2/FlumeData.1471246960903
2016-08-15 15:42:43,328 (hdfs-sink1-roll-timer-0) [INFO - org.apache.flume.sink.hdfs.HDFSEventSink$1.run(HDFSEventSink.java:394)] Writer callback called.
2016-08-15 15:42:45,672 (Log-BackgroundWorker-channel1) [INFO - org.apache.flume.channel.file.EventQueueBackingStoreFile.beginCheckpoint(EventQueueBackingStoreFile.java:230)] Start checkpoint for /tmp/testlog/point/checkpoint, elements to sync = 1
2016-08-15 15:42:45,680 (Log-BackgroundWorker-channel1) [INFO - org.apache.flume.channel.file.EventQueueBackingStoreFile.checkpoint(EventQueueBackingStoreFile.java:255)] Updating checkpoint metadata: logWriteOrderID: 1471246545691, queueSize: 0, queueHead: 0
2016-08-15 15:42:45,685 (Log-BackgroundWorker-channel1) [INFO - org.apache.flume.channel.file.Log.writeCheckpoint(Log.java:1034)] Updated checkpoint for file: /tmp/testlog/log/log-2 position: 226 logWriteOrderID: 1471246545691
...
```

我们查看日志了解flume的执行过程，

### **在hdfs查看内容**

```
# echo `date` this is test log for flume >> /tmp/testlog/data/1.log
# hdfs dfs -ls /log2
Found 2 items
-rw-r--r--   1 root supergroup         70 2016-08-15 12:26 /log2/FlumeData.1471235162707
-rw-r--r--   1 root supergroup         70 2016-08-15 15:42 /log2/FlumeData.1471246960903
# hdfs dfs -cat /log2/FlumeData.1471246960903
2016年 08月 15日 星期一 15:42:36 CST this is test log for flume
 
# cat /tmp/testlog/data/1.log.COMPLETED
2016年 08月 15日 星期一 15:42:36 CST this is test log for flume
# strings /tmp/testlog/log/log-1
E2016
 15:42:36 CST this is test log for flume
```

如果channel用memory的话，更改#set channel1为

```
#set channel1
agent1.channels.channel1.type=memory
agent1.channels.channel1.capacity=1000
 
# flume-ng agent -n agent1 -c conf -f conf/logspool.properties -Dflume.root.logger=INFO,console
 
写入日志
# echo `date` this is test log for flume >> /tmp/testlog/data/2.log 
 
# hdfs dfs -ls /log2
Found 3 items
-rw-r--r--   1 root supergroup         70 2016-08-15 12:26 /log2/FlumeData.1471235162707
-rw-r--r--   1 root supergroup         70 2016-08-15 15:42 /log2/FlumeData.1471246960903
-rw-r--r--   1 root supergroup         70 2016-08-15 16:01 /log2/FlumeData.1471248073191
```

线上我们都是用kafka做数据传输的通道，下面为

### **使用kafka的flume配置**

```
flume的配置：
vim kafka.properties
# Sources, channels, and sinks are defined per
# agent name, in this case flume1.
flume1.sources  = kafka-source-1
flume1.channels = kafka-channel-1
flume1.sinks    = hdfs-sink-1
 
# For each source, channel, and sink, set
# standard properties.
flume1.sources.kafka-source-1.type = org.apache.flume.source.kafka.KafkaSource
flume1.sources.kafka-source-1.zookeeperConnect = vm01:2181,vm02:2181,vm03:2181
flume1.sources.kafka-source-1.topic = log2
flume1.sources.kafka-source-1.batchSize = 5
flume1.sources.kafka-source-1.batchDurationMillis = 200
flume1.sources.kafka-source-1.channels = hdfs-channel-1
flume1.sources.kafka-source-1.kafka.consumer.timeout.ms = 1000
 
flume1.channels.kafka-channel-1.type = org.apache.flume.channel.kafka.KafkaChannel
flume1.channels.kafka-channel-1.brokerList = vm01:9092,vm02:9092,vm03:9092
flume1.channels.kafka-channel-1.topic = log2
flume1.channels.kafka-channel-1.zookeeperConnect = vm01:2181,vm02:2181,vm03:2181
flume1.channels.kafka-channel-1.parseAsFlumeEvent=false
 
flume1.sinks.hdfs-sink-1.channel = kafka-channel-1
flume1.sinks.hdfs-sink-1.type = hdfs
flume1.sinks.hdfs-sink-1.hdfs.writeFormat = Text
flume1.sinks.hdfs-sink-1.hdfs.fileType = DataStream
flume1.sinks.hdfs-sink-1.hdfs.filePrefix = test-events
flume1.sinks.hdfs-sink-1.hdfs.useLocalTimeStamp = true
flume1.sinks.hdfs-sink-1.hdfs.path = hdfs://vm01:9000/log2
flume1.sinks.hdfs-sink-1.hdfs.rollCount=100
flume1.sinks.hdfs-sink-1.hdfs.rollSize=1
 
# specify the capacity of the memory channel.
flume1.channels.kafka-channel-1.capacity = 10000
flume1.channels.kafka-channel-1.transactionCapacity = 10000
 
flume燥起来
# flume-ng agent -n flume1 -c conf -f conf/kafka.properties -Dflume.root.logger=INFO,console
 
向kafka输入日志
# /usr/local/kafka/bin/kafka-console-producer.sh --broker-list 10.211.55.4:9092,10.211.55.5:9092,10.211.55.6:9092 --topic log2
hello,this is test log for kafka
 
查看hdfs中文件
# hdfs dfs -ls /log2
-rw-r--r--   1 root supergroup         33 2016-08-15 16:33 /log2/test-events.1471250014828
# hdfs dfs -cat /log2/test-events.1471250014828
hello,this is test log for kafka
```

sources,channels,sinks三者灵活搭配，如果

### **flume读取日志文件存储到hdfs**

```
flume配置
# cat conf/exec_log.properties
# Define a source, channel, sink
agent1.sources = s1
agent1.channels = c1
agent1.sinks = k1
 
# Configure channel
agent1.channels.c1.type = memory
agent1.channels.c1.capacity = 1000
 
# Configure sources
agent1.sources.s1.channels = c1
agent1.sources.s1.type = exec
agent1.sources.s1.command = tail -F /tmp/1.log
 
# Define a logger sink that simply logs all events it receives
# and connect it to the other end of the same channel.
agent1.sinks.k1.channel = c1
agent1.sinks.k1.type = hdfs
agent1.sinks.k1.hdfs.path = hdfs://vm01:9000/log2
agent1.sinks.k1.hdfs.filePrefix = events-
agent1.sinks.k1.hdfs.round = true
agent1.sinks.k1.hdfs.roundUnit = minute
agent1.sinks.k1.hdfs.roundValue = 1
 
flume起来
# flume-ng agent -n agent1 -c conf -f conf/exec_log.properties -Dflume.root.logger=INFO,console
 
写日志
#vim /tmp/1.log
 
查看日志
# hdfs dfs -ls /log2
-rw-r--r--   1 root supergroup        825 2016-08-15 16:45 /log2/events-.1471250733274
```

通过上面对文件夹的日志收集，flume使用kafka传输，对确定日志文件的传送，获取对应用flume有相应的认识，by [bbotte.com](http://bbotte.com/)

flume参考文章

<https://www.cloudera.com/documentation/kafka/latest/topics/kafka_flume.html>

<http://blog.cloudera.com/blog/2014/11/flafka-apache-flume-meets-apache-kafka-for-event-processing/>

<http://shiyanjun.cn/archives/915.html>

2016年08月15日 于 [linux工匠](https://bbotte.github.io/) 发表

























