---
layout: default
---

# elasticsearch创建index

遇到一个奇怪的问题，每天早上8点就会收到elasticsearch报警

```
告警信息: Unassigned Shards
Cluster status:yellow
```

查看日志报错如下：

```
[2016-08-25 08:00:12,579][DEBUG][action.admin.indices.stats] [node-1] [indices:monitor/stats] failed
 to execute operation for shard [[logstash-2016.08.25][3], node[xxxx],
[R], v[2], s[INITIALIZING], a[id=xxxx], unassigned_info[[reason=INDEX_CREATED], at[2016-08-25T00:00:10.111Z]]]
[logstash-2016.08.25][[logstash-2016.08.25][3]] BroadcastShardOperationFailedException[operation indices:monitor/stats failed]; nested: ShardNotFoundException[no such shard];
        at org.elasticsearch.action.support.broadcast.node.TransportBroadcastByNodeAction$BroadcastByNodeTransportRequestHandler.onShardOperation(TransportBroadcastByNodeAction.java:399)
        at org.elasticsearch.action.support.broadcast.node.TransportBroadcastByNodeAction$BroadcastByNodeTransportRequestHandler.messageReceived(TransportBroadcastByNodeAction.java:376)
        at org.elasticsearch.action.support.broadcast.node.TransportBroadcastByNodeAction$BroadcastByNodeTransportRequestHandler.messageReceived(TransportBroadcastByNodeAction.java:365)
        at org.elasticsearch.transport.netty.MessageChannelHandler$RequestHandler.doRun(MessageChannelHandler.java:299)
        at org.elasticsearch.common.util.concurrent.AbstractRunnable.run(AbstractRunnable.java:37)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1145)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:615)
        at java.lang.Thread.run(Thread.java:745)
Caused by: [logstash-2016.08.25][[logstash-2016.08.25][3]] ShardNotFoundException[no such shard]
        at org.elasticsearch.index.IndexService.shardSafe(IndexService.java:198)
        at org.elasticsearch.action.admin.indices.stats.TransportIndicesStatsAction.shardOperation(TransportIndicesStatsAction.java:98)
        at org.elasticsearch.action.admin.indices.stats.TransportIndicesStatsAction.shardOperation(TransportIndicesStatsAction.java:47)
        at org.elasticsearch.action.support.broadcast.node.TransportBroadcastByNodeAction$BroadcastByNodeTransportRequestHandler.onShardOperation(TransportBroadcastByNodeAction.java:395)
        ... 7 more
```

原因：因为时区的差别，elasticsearch会在格林威治时间生成每天的index，当生成index后集群会同步index信息，造成集群报警，可以通过kopf插件查看状态。因此写个脚本，提前创建index

```
cat createESindex.py
#!/usr/bin/env python
#ecoding=utf8
#提前一天创建es的index
#pip install elasticsearch
import datetime
import re
from elasticsearch import Elasticsearch
import time
 
es = Elasticsearch('127.0.0.1:9200',timeout=5.0)
#获取indices
result = es.cat.indices()
data = result.splitlines()
 
d = datetime.datetime.now().strftime("%Y.%m.%d")
l = [i for i in data if re.compile(d).search(i) is not None ]
 
tomorrow = str(datetime.date.today() + datetime.timedelta(days=1)).replace('-','.')
year = str(datetime.date.today().year)
for i in range(len(l)):
    esIndex = re.split(year,list(re.split(r' ',l[i]))[2])[0] + tomorrow
    print "create es index %s" % (esIndex)
    time.sleep(23)
    es.indices.create(index=esIndex)
```

创建index中间sleep 23s

2016年09月30日 于 [linux工匠](https://bbotte.github.io/) 发表





























