# kubernetes安装redis cluster集群

redis cluster集群自带哨兵，自带主从切换，master节点最少3个，如果没有slave节点，那么当master节点故障后，数据就不完整

不管是gfs或者nfs首先要创建volume
假如gfs是2个节点，并且节点名字为k8sgfs1、k8sgfs2

```
for i in {0..5};do gluster volume create def-redis${i} replica 2 transport tcp k8sgfs1:/data/defredis${i} k8sgfs2:/data/defredis${i} force;done
for i in {0..5};do gluster volume start def-redis${i};done
```

再创建pv

```
# cat def-pv.yaml 
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: datadir-redis1
  namespace: default
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteMany
  glusterfs:
    endpoints: "defgfs-ep"
    path: "def-redis0"
    readOnly: false
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: datadir-redis2
  namespace: default
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteMany
  glusterfs:
    endpoints: "defgfs-ep"
    path: "def-redis1"
    readOnly: false
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: datadir-redis3
  namespace: default
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteMany
  glusterfs:
    endpoints: "defgfs-ep"
    path: "def-redis2"
    readOnly: false
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: datadir-redis4
  namespace: default
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteMany
  glusterfs:
    endpoints: "defgfs-ep"
    path: "def-redis3"
    readOnly: false
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: datadir-redis5
  namespace: default
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteMany
  glusterfs:
    endpoints: "defgfs-ep"
    path: "def-redis4"
    readOnly: false
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: datadir-redis6
  namespace: default
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteMany
  glusterfs:
    endpoints: "defgfs-ep"
    path: "def-redis5"
    readOnly: false
```

用statefluset创建redis cluster节点，这里创建redis服务名为 redis-com，代码连此redis为： redis-com:6379

redis的Dockerfile 请点击<https://github.com/bbotte/bbotte.com/tree/master/Commonly-Dockerfile/redis>

```
cat redis-cluster.yaml
---
apiVersion: v1
kind: Service
metadata:
  name: redis-com
  namespace: default
spec:
  type: ClusterIP
  ports:
  - port: 6379
    targetPort: 6379
    name: client
  - port: 16379
    targetPort: 16379
    name: gossip
  selector:
    app: redis-cluster
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-cluster
  namespace: default
data:
  update-node.sh: |+
    #!/bin/sh
    REDIS_NODES="/data/redis/nodes.conf"
    sed -i -e "/myself/ s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}/${POD_IP}/" ${REDIS_NODES}
    exec "$@"
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
  namespace: default
spec:
  serviceName: redis-com
  replicas: 6
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      terminationGracePeriodSeconds: 20
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - redis
              topologyKey: kubernetes.io/hostname
      initContainers:
      - name: disable-thp
        image: harbor.bbotte.com/k8s/busybox
        command: ['/bin/sh','-c','echo never > /sys/kernel/mm/transparent_hugepage/enabled && sysctl -w net.core.somaxconn=65535 && sleep 1',"/conf/update-node.sh"]
        imagePullPolicy: IfNotPresent
        securityContext:
          privileged: true
        volumeMounts:
        - mountPath: /sys
          name: sys
          readOnly: false
      containers:
      - name: redis
        image: harbor.bbotte.com/devops/redis:0.11
        ports:
        - containerPort: 6379
          name: client
        - containerPort: 16379
          name: gossip
        env:
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        - name: REDISCLUSTER
          value: "yes"
        - name: DATADIR
          value: "/data/redis/"
        volumeMounts:
        - name: conf
          mountPath: /conf
          readOnly: false
        - name: datadir
          mountPath: /data
          readOnly: false
      imagePullSecrets:
        - name: harbor-auth-def
      volumes:
      - name: conf
        configMap:
          name: redis-cluster
          defaultMode: 0755
      - name: sys
        hostPath:
          path: /sys
  volumeClaimTemplates:
  - metadata:
      name: datadir
    spec:
      accessModes: [ "ReadWriteMany" ]
      resources:
        requests:
          storage: 2Gi
```

创建后查看k8s集群状态

```
# kubectl get pvc
NAME                      STATUS   VOLUME               CAPACITY   ACCESS MODES   STORAGECLASS   AGE
datadir-redis-cluster-0   Bound    datadir-redis1       2Gi        RWX             80m
datadir-redis-cluster-1   Bound    datadir-redis2       2Gi        RWX             80m
datadir-redis-cluster-2   Bound    datadir-redis3       2Gi        RWX             80m
datadir-redis-cluster-3   Bound    datadir-redis6       2Gi        RWX             80m
datadir-redis-cluster-4   Bound    datadir-redis5       2Gi        RWX             80m
datadir-redis-cluster-5   Bound    datadir-redis4       2Gi        RWX             80m

# kubectl get all
NAME                  READY   STATUS    RESTARTS   AGE
pod/redis-cluster-0   1/1     Running   0          81m
pod/redis-cluster-1   1/1     Running   0          81m
pod/redis-cluster-2   1/1     Running   0          81m
pod/redis-cluster-3   1/1     Running   0          80m
pod/redis-cluster-4   1/1     Running   0          80m
pod/redis-cluster-5   1/1     Running   0          80m

NAME                 TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)              AGE
service/defgfs-svc   ClusterIP   10.200.15.185   <none>        1/TCP                20h
service/kubernetes   ClusterIP   10.200.0.1      <none>        443/TCP              61d
service/redis-com    ClusterIP   10.200.29.208   <none>        6379/TCP,16379/TCP   81m

NAME                             READY   AGE
statefulset.apps/redis-cluster   6/6     81m

```

redis集群创建完毕，那么需要做集群初始化，如果redis版本大于5

```
kubectl exec -it redis-cluster-0 -- redis-cli --cluster create --cluster-replicas 1 $(kubectl get pods -l app=redis-cluster -o jsonpath='{range.items[*]}{.status.podIP}:6379 ')
kubectl exec -it redis-cluster-0 -- redis-cli cluster info
```

redis版本小于5
我们纯手工做redis cluster

3个主节点分别分配槽位

```
# kubectl exec -it redis-cluster-0 /bin/bash
bash-4.4# for i in {0..5461};do redis-cli -p 6379 cluster addslots $i 2>&1 >/dev/null;done
bash-4.4# exit
```

```
# kubectl exec -it redis-cluster-1 /bin/bash
bash-4.4# for i in {5462..10922};do redis-cli -p 6379 cluster addslots $i 2>&1 >/dev/null;done
bash-4.4# exit
```

```
# kubectl exec -it redis-cluster-2 /bin/bash
bash-4.4# for i in {10923..16383};do redis-cli -p 6379 cluster addslots $i 2>&1 >/dev/null;done
```

16384个槽位分配完毕
顺便在redis-cluster-2上添加其他节点

```
redis-cli -c -p 6379 cluster meet `dig +short redis-cluster-0.redis-com.default.svc.cluster.local` 6379
redis-cli -c -p 6379 cluster meet `dig +short redis-cluster-1.redis-com.default.svc.cluster.local` 6379
redis-cli -c -p 6379 cluster meet `dig +short redis-cluster-3.redis-com.default.svc.cluster.local` 6379
redis-cli -c -p 6379 cluster meet `dig +short redis-cluster-4.redis-com.default.svc.cluster.local` 6379
redis-cli -c -p 6379 cluster meet `dig +short redis-cluster-5.redis-com.default.svc.cluster.local` 6379
```

查看状态，此时集群状态cluster info 应该为ok

```
bash-4.4# redis-cli -c -p 6379 cluster nodes
c8b40385a4814949b388b5cb7be5cf6048350a30 10.100.6.82:6379@16379 master - 0 1567590187713 3 connected
b9aec2f91ffa42b394445454b5113daa4a148766 10.100.3.149:6379@16379 myself,master - 0 1567590185000 2 connected 10923-16383
c49ba9724b78ca20f4a91efc9e9a586695bde451 10.100.4.8:6379@16379 master - 0 1567590186712 5 connected
5239934bf7eea306c9f21fee10042cb53ad45c7d 10.100.7.33:6379@16379 master - 0 1567590186000 1 connected 0-5461
ed1ea8b44e5ea3ba9008a2232faa1af3c8e7a18f 10.100.5.204:6379@16379 master - 0 1567590185711 0 connected
8d139957bb4fc76ceb4f43cd2e824d2ba59e0774 10.100.4.9:6379@16379 master - 0 1567590187000 4 connected 5462-10922
bash-4.4# redis-cli -c -p 6379 cluster info
cluster_state:ok
cluster_slots_assigned:16384
cluster_slots_ok:16384
cluster_slots_pfail:0
cluster_slots_fail:0
cluster_known_nodes:6
cluster_size:3
cluster_current_epoch:5
cluster_my_epoch:2
cluster_stats_messages_ping_sent:100
cluster_stats_messages_pong_sent:118
cluster_stats_messages_meet_sent:5
cluster_stats_messages_sent:223
cluster_stats_messages_ping_received:118
cluster_stats_messages_pong_received:105
cluster_stats_messages_received:223
bash-4.4# exit
```

登录每个从节点做从库

```
# kubectl exec -it redis-cluster-3 /bin/bash
bash-4.4# redis-cli -c -p 6379 cluster replicate `redis-cli -c -p 6379 cluster nodes|grep "0-5461"|awk '{print $1}'`
OK
bash-4.4# exit
```

```
# kubectl exec -it redis-cluster-4 /bin/bash
bash-4.4# redis-cli -c -p 6379 cluster replicate `redis-cli -c -p 6379 cluster nodes|grep "5462-10922"|awk '{print $1}'`
OK
bash-4.4# exit
```

```
# kubectl exec -it redis-cluster-5 /bin/bash
bash-4.4# redis-cli -c -p 6379 cluster replicate `redis-cli -c -p 6379 cluster nodes|grep "10923-16383"|awk '{print $1}'`
OK
bash-4.4# redis-cli -c -p 6379 cluster nodes
c8b40385a4814949b388b5cb7be5cf6048350a30 10.100.6.82:6379@16379 slave 8d139957bb4fc76ceb4f43cd2e824d2ba59e0774 0 1567590518718 4 connected
c49ba9724b78ca20f4a91efc9e9a586695bde451 10.100.4.8:6379@16379 slave 5239934bf7eea306c9f21fee10042cb53ad45c7d 0 1567590518000 5 connected
b9aec2f91ffa42b394445454b5113daa4a148766 10.100.3.149:6379@16379 master - 0 1567590518000 2 connected 10923-16383
ed1ea8b44e5ea3ba9008a2232faa1af3c8e7a18f 10.100.5.204:6379@16379 myself,slave b9aec2f91ffa42b394445454b5113daa4a148766 0 1567590519000 0 connected
8d139957bb4fc76ceb4f43cd2e824d2ba59e0774 10.100.4.9:6379@16379 master - 0 1567590519722 4 connected 5462-10922
5239934bf7eea306c9f21fee10042cb53ad45c7d 10.100.7.33:6379@16379 master - 0 1567590520725 1 connected 0-5461
bash-4.4# 
```

验证

redis添加些数据看一下

```
bash-4.4# redis-cli -c -p 6379
127.0.0.1:6379> set k1 v1
-> Redirected to slot [12706] located at 10.100.3.149:6379
OK
10.100.3.149:6379> set k2 v2
-> Redirected to slot [449] located at 10.100.7.33:6379
OK
10.100.7.33:6379> set k3 v3
OK
10.100.7.33:6379> set k4 v4
-> Redirected to slot [8455] located at 10.100.4.9:6379
OK
10.100.7.33:6379> get k1
-> Redirected to slot [12706] located at 10.100.3.149:6379
"v1"
10.100.3.149:6379> quit
bash-4.4# exit

for i in {0..5};do kubectl exec -it redis-cluster-${i} -- redis-cli -c info replication|egrep "role|master_host";done
```

验证集群，把redis 1 停止，查看状态

```
# redis-cli -c -p 6679
127.0.0.1:6379> cluster nodes
127.0.0.1:6379> cluster info
127.0.0.1:6379> info replication
```

把redis 1 启动，查看状态

```
# redis-cli -c -p 6379
127.0.0.1:6379> info replication
```

结论：当主节点故障，从节点接替，并成为主节点。故障节点恢复正常后，自动假如集群，并成为从节点

删除此redis集群

```
kubectl delete -f redis-cluster.yaml
for i in {0..5};do kubectl delete pvc datadir-redis-cluster-${i};done
kubectl delete -f def-pv.yaml 
清空gfs磁盘文件
```

