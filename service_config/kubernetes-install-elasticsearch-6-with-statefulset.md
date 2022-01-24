---
layout: default
---


# 在kubernetes中statefu方式安装elasticsearch-6集群

存储使用glusterfs，3个节点，es的service名称为 es-svc,es版本是6

```
# for i in {0..2};do gluster volume create es-cluster${i} replica 3 transport tcp gfs1:/gfs/es${i} gfs2:/gfs/es${i} gfs3:/gfs/es${i} force;done
volume create: es-cluster0: success: please start the volume to access data
volume create: es-cluster1: success: please start the volume to access data
volume create: es-cluster2: success: please start the volume to access data

# for i in {0..2};do gluster volume start es-cluster${i};done
volume start: es-cluster0: success
volume start: es-cluster1: success
volume start: es-cluster2: success

```

创建pv

```
# cat es-pv.yaml
apiVersion: v1
kind: Endpoints
metadata:
  name: gfsep-es
  namespace: default
subsets:
- addresses:
  - ip: 192.168.3.100
  - ip: 192.168.3.101
  - ip: 192.168.3.102
  ports:
  - port: 11
    protocol: TCP
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-es1
  namespace: default
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteMany
  glusterfs:
    endpoints: "gfsep-es"
    path: "es-cluster0"
    readOnly: false
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-es2
  namespace: default
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteMany
  glusterfs:
    endpoints: "gfsep-es"
    path: "es-cluster1"
    readOnly: false
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-es3
  namespace: default
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteMany
  glusterfs:
    endpoints: "gfsep-es"
    path: "es-cluster2"
    readOnly: false

```

es的RBAC权限设置

```
# cat es-rbac.yaml 
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: es
  namespace: default
---
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: es
  namespace: default
rules:
- apiGroups: [""]
  resources: ["endpoints"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: es
  namespace: default
subjects:
- kind: ServiceAccount
  name: es
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: es
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: es
  namespace: default
rules:
  - apiGroups: [""]
    resources: ["persistentvolumes"]
    verbs: ["get", "list", "watch", "create", "delete"]
  - apiGroups: [""]
    resources: ["persistentvolumeclaims"]
    verbs: ["get", "list", "watch", "update"]
  - apiGroups: ["storage.k8s.io"]
    resources: ["storageclasses"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["create", "update", "patch"]
  - apiGroups: [""]
    resources: ["services", "endpoints"]
    verbs: ["get"]
  - apiGroups: ["extensions"]
    resources: ["podsecuritypolicies"]
    resourceNames: ["nfs-provisioner"]
    verbs: ["use"]
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: es
subjects:
  - kind: ServiceAccount
    name: es
    namespace: default 
roleRef:
  kind: ClusterRole
  name: es
  apiGroup: rbac.authorization.k8s.io

```

下面为es的配置文件，es的service name官网写的是elasticsearch-discovery，通过变量可以替换

```
# cat es-cm.yaml 
apiVersion: v1
kind: ConfigMap
metadata:
  name: es-cm
  namespace: default
data:
  elasticsearch.yml: |
    node.data: ${NODE_DATA:true}
    node.master: ${NODE_MASTER:true}
    node.ingest: ${NODE_INGEST:true}
    node.name: ${HOSTNAME}
    network.host: 0.0.0.0
    bootstrap.memory_lock: ${BOOTSTRAP_MEMORY_LOCK:false}
    discovery:
      zen:
        ping.unicast.hosts: ${DISCOVERY_SERVICE:elasticsearch-discovery}
        minimum_master_nodes: ${MINIMUM_MASTER_NODES:2}
    processors: ${PROCESSORS:}
    gateway.expected_master_nodes: ${EXPECTED_MASTER_NODES:2}
    gateway.expected_data_nodes: ${EXPECTED_DATA_NODES:1}
    gateway.recover_after_time: ${RECOVER_AFTER_TIME:5m}
    gateway.recover_after_master_nodes: ${RECOVER_AFTER_MASTER_NODES:2}
    gateway.recover_after_data_nodes: ${RECOVER_AFTER_DATA_NODES:1}

  log4j2.properties: |-
    status = error
    appender.console.type = Console
    appender.console.name = console
    appender.console.layout.type = PatternLayout
    appender.console.layout.pattern = [%d{ISO8601}][%-5p][%-25c{1.}] %marker%m%n
    rootLogger.level = info
    rootLogger.appenderRef.console.ref = console
    logger.searchguard.name = com.floragunn
    logger.searchguard.level = info

```

最后是es的statefulset文件

```
# cat es-ss.yaml 
kind: StatefulSet
apiVersion: apps/v1
metadata:
  name: es
  namespace: default
spec:
  serviceName: es-svc
  replicas: 3
  selector:
    matchLabels:
      app: es
  template:
    metadata:
      labels:
        app: es
    spec:
      initContainers:
      - name: init
        image: busybox:1.32.0
        command: ['/bin/sh','-c','sysctl -w vm.max_map_count=262144 && sleep 1']
        imagePullPolicy: IfNotPresent
        securityContext:
          privileged: true
      - name: chown
        image: busybox:1.32.0
        command: ['/bin/sh','-c','chown -R 1000:1000 /usr/share/elasticsearch/data']
        imagePullPolicy: IfNotPresent
        securityContext:
          privileged: true
        volumeMounts:
          - name: es-data
            mountPath: /usr/share/elasticsearch/data
      serviceAccount: es
      containers:
      - name: es
        #image: elasticsearch:6.8.13
        image: docker.elastic.co/elasticsearch/elasticsearch-oss:6.8.13
        imagePullPolicy: IfNotPresent
        resources:
          limits:
            cpu: 2
            memory: 2G
          requests:
            cpu: 500m
            memory: 512Mi
        ports:
        - containerPort: 9200
          name: http
        - containerPort: 9300
          name: transport
        readinessProbe:
          httpGet:
            path: /_cluster/health?local=true
            port: 9200
          initialDelaySeconds: 10
          periodSeconds: 20
          timeoutSeconds: 10
        env:
        - name: node.name
          valueFrom:
            fieldRef:
              apiVersion: v1
              fieldPath: metadata.name
        - name: cluster.name
          value: es-cluster
        - name: DISCOVERY_SERVICE
          value: "es-svc"
        - name: ES_JAVA_OPTS
          value: "-Djava.net.preferIPv4Stack=true -Xms1G -Xmx1G"
        volumeMounts:
          - name: es-data
            mountPath: /usr/share/elasticsearch/data
          - mountPath: /usr/share/elasticsearch/config/elasticsearch.yml
            name: config
            subPath: elasticsearch.yml
          - mountPath: /usr/share/elasticsearch/config/log4j2.properties
            name: log4j2
            subPath: log4j2.properties
#          - name: es-plugins
#            mountPath: /usr/share/elasticsearch/plugins
      imagePullSecrets:
        - name: harbor-pxx
      volumes:
      - name: config
        configMap:
          name: es-cm
      - name: log4j2
        configMap:
          name: es-cm
#      - name: es-plugins
#        persistentVolumeClaim:
#          claimName: es-plugin
  volumeClaimTemplates:
  - metadata:
      name: es-data
    spec:
      accessModes: [ "ReadWriteMany" ]
      resources:
        requests:
          storage: 10Gi

---
kind: Service
apiVersion: v1
metadata:
  name: es-svc
  namespace: default
  labels:
    app: es
spec:
  type: NodePort
  selector:
    app: es
  ports:
  - port: 9200
    name: es9200
    targetPort: 9200
    nodePort: 30920
  - port: 9300
    name: es9300
    targetPort: 9300

```

服务已经完成，查看创建的pod，查看集群是否正常

```
# kubectl get po|grep es
es-0                                     1/1     Running   0              9m5s
es-1                                     1/1     Running   0              8m3s
es-2                                     1/1     Running   0              7m41s

# kubectl exec -it es-0 bash
[root@es-0 elasticsearch]# curl -XGET 'http://localhost:9200/_cluster/stats?human&pretty'|head
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  3496  100  3496    0     0  85684      0 --:--:-- --:--:-- --:--:-- 87400
{
  "_nodes" : {
    "total" : 3,
    "successful" : 3,
    "failed" : 0
  },
  "cluster_name" : "es-cluster",
  "cluster_uuid" : "ra0XTldhQRWxHXzG_X9YM0",
  "timestamp" : 1641970728295,
  "status" : "green",

```

删除集群

```
kubectl delete -f es-ss.yaml 
kubectl delete pvc/es-data-es-2
kubectl delete pvc/es-data-es-1
kubectl delete pvc/es-data-es-0
kubectl delete pv/pv-es3
kubectl delete pv/pv-es2
kubectl delete pv/pv-es1

```

2021年01月12日 于 [linux工匠](https://bbotte.github.io/) 发表