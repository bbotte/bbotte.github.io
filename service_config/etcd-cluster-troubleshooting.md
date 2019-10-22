# etcd集群故障处理

### etcd安装

```
rpm -ivh etcd-3.2.15-1.el7.x86_64.rpm
systemctl daemon-reload
systemctl enable etcd
systemctl start etcd
export ETCDCTL_API=3
systemctl status etcd
```

hosts如下

```
192.168.0.100 etcd01
192.168.0.101 etcd02
192.168.0.102 etcd03
```

### etcd配置

etcd02配置如下，详细见[kubernetes1.9版本集群配置向导](https://bbotte.github.io/virtualization/kubernetes_cluster_install_1.9.4)

```
# egrep -v "^$|^#" /etc/etcd/etcd.conf 
ETCD_DATA_DIR="/var/lib/etcd/"
ETCD_LISTEN_PEER_URLS="https://192.168.0.101:2380"
ETCD_LISTEN_CLIENT_URLS="https://192.168.0.101:2379,http://127.0.0.1:2379"
ETCD_NAME="etcd02"
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://192.168.0.101:2380"
ETCD_ADVERTISE_CLIENT_URLS="https://192.168.0.101:2379"
ETCD_INITIAL_CLUSTER="etcd01=https://192.168.0.100:2380,etcd02=https://192.168.0.101:2380,etcd03=https://192.168.0.102:2380"
ETCD_INITIAL_CLUSTER_TOKEN="etcd-cluster"
ETCD_INITIAL_CLUSTER_STATE="existing"
ETCD_CERT_FILE="/etc/kubernetes/ssl/etcd.pem"
ETCD_KEY_FILE="/etc/kubernetes/ssl/etcd-key.pem"
ETCD_CLIENT_CERT_AUTH="true"
ETCD_TRUSTED_CA_FILE="/etc/kubernetes/ssl/ca.pem"
ETCD_AUTO_TLS="true"
ETCD_PEER_CERT_FILE="/etc/kubernetes/ssl/etcd.pem"
ETCD_PEER_KEY_FILE="/etc/kubernetes/ssl/etcd-key.pem"
ETCD_PEER_CLIENT_CERT_AUTH="true"
ETCD_PEER_TRUSTED_CA_FILE="/etc/kubernetes/ssl/ca.pem"
ETCD_PEER_AUTO_TLS="true"
```

### 故障报错

3个节点做集群，直接关机后，etcd02故障，报错：

```
etcd: advertise client URLs = https://192.168.0.101:2379
etcd: read wal error (wal: crc mismatch) and cannot be repaired
systemd: etcd.service: main process exited, code=exited, status=1/FAILURE
```

wal的cec校验出错，谷歌了一下，没什么结果，于是移除这个etcd，再恢复
在正常的etcd节点移除

```
# etcdctl member list
1ce6d6d01109192, started, etcd03, https://192.168.0.102:2380, https://192.168.0.102:2379
9b534175b46ea789, started, etcd01, https://192.168.0.100:2380, https://192.168.0.100:2379
ac2f188e97f50eb7, started, etcd02, https://192.168.0.101:2380, https://192.168.0.101:2379
# etcdctl member remove ac2f188e97f50eb7
Member ac2f188e97f50eb7 removed from cluster 194cd14a48430083
```

再启动etcd服务

```
# systemctl start etcd
```

报错：

```
etcd: error validating peerURLs {ClusterID:194cd14a48430083 Members:[&{ID:1ce6d6d01109192 RaftAttributes:{PeerURLs:[https://192.168.0.102:2380]} Attributes:{Name:etcd03 ClientURLs:[https://192.168.0.102:2379]}} &{ID:9b534175b46ea789 RaftAttributes:{PeerURLs:[https://192.168.0.100:2380]} Attributes:{Name:etcd01 ClientURLs:[https://192.168.0.100:2379]}}] RemovedMemberIDs:[]}: member count is unequal
```

```
etcd: the member has been permanently removed from the cluster the data-dir used by this member must be removed
```

### etcd恢复数据

在etcd02节点恢复一下数据试试：

```
# mv /var/lib/etcd/member /var/lib/member
# rm -rf /var/lib/etcd/*
# etcdctl snapshot restore /var/lib/member/snap/db --skip-hash-check=true
2018-06-22 11:28:35.622666 I | mvcc: restore compact to 10177401
2018-06-22 11:28:35.659626 I | etcdserver/membership: added member 8e9e05c52164694d [http://localhost:2380] to cluster cdf818194e3a8c32
# systemctl start etcd
```

服务启动了，自己把自己选做主，服务倒是启动了，加入集群还是出错，用正常的节点备份再恢复

```
# etcdctl snapshot save etcdback.db

# etcdctl member add etcd02 http://192.168.0.101:2380
Error: member name not provided.
```

看看现在集群的其他2个etcd

```
# curl -k --key /etc/kubernetes/ssl/etcd-key.pem --cert /etc/kubernetes/ssl/etcd.pem https://192.168.0.100:2380/members
[{"id":130161754177048978,"peerURLs":["https://192.168.0.102:2380"],"name":"etcd03","clientURLs":["https://192.168.0.102:2379"]},{"id":11192361472739944329,"peerURLs":["https://192.168.0.100:2380"],"name":"etcd01","clientURLs":["https://192.168.0.100:2379"]}]
```

参考文档：
etcdctl member add etcd_name –peer-urls=”https://peerURLs”
再次添加

```
# etcdctl member add etcd02 --peer-urls="https://192.168.0.101:2380"
Member 41c2a7b938a5e387 added to cluster 194cd14a48430083
 
ETCD_NAME="etcd02"
ETCD_INITIAL_CLUSTER="etcd03=https://192.168.0.102:2380,etcd02=https://192.168.0.101:2380,etcd01=https://192.168.0.100:2380"
ETCD_INITIAL_CLUSTER_STATE="existing"
```

查看etcd member状态：

```
# etcdctl member list
1ce6d6d01109192, started, etcd03, https://192.168.0.102:2380, https://192.168.0.102:2379
9b534175b46ea789, started, etcd01, https://192.168.0.100:2380, https://192.168.0.100:2379
ad17c3da831c84c7, unstarted, , https://192.168.0.101:2380,
```

报错：

```
etcd: request cluster ID mismatch (got 194cd14a48430083 want cdf818194e3a8c32)
```

发现步骤顺序错误，应该是先添加到etcd集群，再启动etcd服务，我们现在先启动etcd服务，就是一个etcd单点

### etcd节点加入集群

故障的etcd主机：

```
# systemctl stop etcd
```

正常的etcd主机：

```
# etcdctl member remove ad17c3da831c84c7
```

```
# etcdctl member add etcd02 --peer-urls="https://192.168.0.101:2380"
Member 41c2a7b938a5e387 added to cluster 194cd14a48430083
 
ETCD_NAME="etcd02"
ETCD_INITIAL_CLUSTER="etcd03=https://192.168.0.102:2380,etcd02=https://192.168.0.101:2380,etcd01=https://192.168.0.100:2380"
ETCD_INITIAL_CLUSTER_STATE="existing"
```

故障的etcd主机，启动etcd后，再查看etcd状态：

```
# 先删除错误节点的数据
# rm -rf /var/lib/etcd/member
# systemctl start etcd
# 等待一会，这时候会同步数据，稍等再查看节点状态
# etcdctl endpoint health
127.0.0.1:2379 is healthy: successfully committed proposal: took = 24.52485ms
```

$$

$$

```
# etcdctl member list
1ce6d6d01109192, started, etcd03, https://192.168.0.102:2380, https://192.168.0.102:2379
41c2a7b938a5e387, started, etcd02, https://192.168.0.101:2380, https://192.168.0.101:2379
9b534175b46ea789, started, etcd01, https://192.168.0.100:2380, https://192.168.0.100:2379
```

到这里，etcd故障修复完毕

### etcd常用命令

查看状态

```
# export ETCDCTL_API=3
 
# etcdctl endpoint status --write-out=table
+----------------+------------------+---------+---------+-----------+-----------+------------+
|    ENDPOINT    |        ID        | VERSION | DB SIZE | IS LEADER | RAFT TERM | RAFT INDEX |
+----------------+------------------+---------+---------+-----------+-----------+------------+
| 127.0.0.1:2379 | 41c2a7b938a5e387 |  3.2.15 |   15 MB |      true |       317 |   11051403 |
+----------------+------------------+---------+---------+-----------+-----------+------------+
```

备份及恢复

```
etcdctl snapshot save etcdback.db
etcdctl snapshot status etcdback.db --write-out=table
etcdctl snapshot restore etcdback.db --skip-hash-check=true
```

etcd监控

```
# curl -L http://localhost:2379/metrics
# HELP etcd_debugging_mvcc_keys_total Total number of keys.
# TYPE etcd_debugging_mvcc_keys_total gauge
etcd_debugging_mvcc_keys_total 776
# HELP etcd_debugging_mvcc_pending_events_total Total number of pending events to be sent.
# TYPE etcd_debugging_mvcc_pending_events_total gauge
etcd_debugging_mvcc_pending_events_total 0
# HELP etcd_debugging_mvcc_put_total Total number of puts seen by this member.
# TYPE etcd_debugging_mvcc_put_total counter
etcd_debugging_mvcc_put_total 9.548201e+06
# HELP etcd_debugging_mvcc_range_total Total number of ranges seen by this member.
# TYPE etcd_debugging_mvcc_range_total counter
etcd_debugging_mvcc_range_total 2.1052143e+07
# HELP etcd_debugging_mvcc_slow_watcher_total Total number of unsynced slow watchers.
# TYPE etcd_debugging_mvcc_slow_watcher_total gauge
etcd_debugging_mvcc_slow_watcher_total 0
# HELP etcd_debugging_mvcc_txn_total Total number of txns seen by this member.
# TYPE etcd_debugging_mvcc_txn_total counter
etcd_debugging_mvcc_txn_total 0
# HELP etcd_debugging_mvcc_watch_stream_total Total number of watch streams.
# TYPE etcd_debugging_mvcc_watch_stream_total gauge
etcd_debugging_mvcc_watch_stream_total 125
# HELP etcd_debugging_mvcc_watcher_total Total number of watchers.
# TYPE etcd_debugging_mvcc_watcher_total gauge
etcd_debugging_mvcc_watcher_total 125
# HELP etcd_debugging_server_lease_expired_total The total number of expired leases.
# TYPE etcd_debugging_server_lease_expired_total counter
etcd_debugging_server_lease_expired_total 3649
```

适合用prometheus监控

```
global:
  scrape_interval: 10s
scrape_configs:
  - job_name: etcd
    static_configs:
    - targets: ['192.168.0.100:2379','192.168.0.101:2379','192.168.0.102:2379']
```

[图解raft算法](http://thesecretlivesofdata.com/raft/)

etcd获取kubernetes的数据

```
# export ETCDCTL_API=3
# etcdctl get /registry/namespaces/default --prefix -w json|python -m json.tool
{
    "count": 1,
    "header": {
        "cluster_id": 1823062066148343939,
        "member_id": 11192361472739944329,
        "raft_term": 317,
        "revision": 10880816
    },
    "kvs": [
        {
            "create_revision": 6,
            "key": "L3JlZ2lzdHJ5L25hbWVzcGFjZXMvZGVmYXVsdA==",
            "mod_revision": 6,
            "value": "azhzAAoPCgJ2MRIJTmFtZXNwYWNlEl8KRQoHZGVmYXVsdBIAGgAiACokOTVlNzdjMWEtM2Q1Ny0xMWU4LTk5YzItMDA1MDU2YmU3NWEzMgA4AEIICK7qttYFEAB6ABIMCgprdWJlcm5ldGVzGggKBkFjdGl2ZRoAIgA=",
            "version": 1
        }
    ]
}
```

查看key的内容

```
# echo L3JlZ2lzdHJ5L25hbWVzcGFjZXMvZGVmYXVsdA== |base64 -d
/registry/namespaces/default
```

```
#!/bin/bash
# Get kubernetes keys from etcd
export ETCDCTL_API=3
keys=`etcdctl get /registry --prefix -w json|python -m json.tool|grep key|cut -d ":" -f2|tr -d '"'|tr -d ","`
for x in $keys;do
  echo $x|base64 -d|sort
done
```

获取etcd中kubernetes所有对象的key

etcd理论 [手把手教你学习 etcd](https://mp.weixin.qq.com/s?__biz=MzA5OTAyNzQ2OA==&mid=2649698318&idx=1&sn=3daa95ab6d891d269b25b0bc3fce4f90&chksm=88930f6dbfe4867be4c7aae46c7fd332e1211bf38e116d25d166eba90ea1e7e20073143a1bfc&scene=0#rd)

2018年06月24日 于 [linux工匠](http://www.bbotte.com/) 发表