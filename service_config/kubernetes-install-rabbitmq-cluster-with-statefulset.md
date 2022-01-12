---
layout: default
---

# 在kubernetes中statefu方式安装rabbitmq集群

为何不用rabbitmq官方的[RabbitMQ Cluster Operator](https://www.rabbitmq.com/kubernetes/operator/operator-overview.html)? 因为官方的operator比较复杂，哪怕使用了bitnami的charts（helm）， 比如需求是更改服务名称、更改mq的一个参数、每次重启pod存储目录不变。如果认为官方的更好用，下面文字可忽略

下面创建的rabbitmq集群，服务名为 rabbitmq-svc，namespace为 default，改为你自己所需要的service name，k8s集群中的rabbitmq，添加了rabbitmq_peer_discovery_k8s 插件，见 [peer-discovery-k8s](https://www.rabbitmq.com/cluster-formation.html#peer-discovery-k8s)

statefulset需要使用动态pv，那么先创建pv，加入使用存储为glusterfs

三台gfs主机名称为：gfs1、gfs2、gfs3，在glusterfs主机创建volume

```bash
for i in {0..2};do gluster volume create mq-cluster${i} replica 3 transport tcp gfs1:/gfs/rabbitmq${i} gfs2:/gfs/rabbitmq${i} gfs3:/gfs/rabbitmq${i} force;done
for i in {0..2};do gluster volume start mq-cluster${i};done

```

---

不管用nas或者gfs，都需要创建pv，这里用gfs，接下来新建pv，

```
apiVersion: v1
kind: Endpoints
metadata:
  name: gfs-ep
  namespace: default
subsets:
- addresses:
  - ip: 192.168.3.100
  - ip: 192.168.3.101
  - ip: 192.168.3.102
  ports:
  - port: 10
    protocol: TCP
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-mq1
  namespace: default
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteMany
  glusterfs:
    endpoints: "gfs-ep"
    path: "mq-cluster0"
    readOnly: false
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-mq2
  namespace: default
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteMany
  glusterfs:
    endpoints: "gfs-ep"
    path: "mq-cluster1"
    readOnly: false
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-mq3
  namespace: default
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteMany
  glusterfs:
    endpoints: "gfs-ep"
    path: "mq-cluster2"
    readOnly: false

```

---

设置RBAC

```
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: rabbitmq
  namespace: default
---
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: rabbitmq
  namespace: default
rules:
- apiGroups: [""]
  resources: ["endpoints"]
  verbs: ["get"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: rabbitmq
  namespace: default
subjects:
- kind: ServiceAccount
  name: rabbitmq
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: rabbitmq


```

---

设置rabbitmq的配置，configmap

```
apiVersion: v1
kind: ConfigMap
metadata:
  name: rabbitmq-config
  namespace: default
data:
  enabled_plugins: |
    [rabbitmq_peer_discovery_k8s, rabbitmq_management, rabbitmq_prometheus].
  rabbitmq.conf: |
    cluster_formation.peer_discovery_backend = k8s
    cluster_formation.k8s.host = kubernetes.default.svc.cluster.local
    cluster_formation.k8s.address_type = hostname
    cluster_formation.k8s.service_name = rabbitmq-svc
    cluster_formation.k8s.hostname_suffix = .rabbitmq-svc.default.svc.cluster.local
    queue_master_locator=min-masters
    cluster_formation.node_cleanup.interval = 30
    loopback_users.guest = false
    vm_memory_high_watermark.relative = 0.6
```

---

最后，创建rabbitmq的statefulset

```
kind: StatefulSet
apiVersion: apps/v1
metadata:
  name: rabbitmq
  namespace: default
spec:
  serviceName: rabbitmq-svc
  replicas: 3
  selector:
    matchLabels:
      app: rabbitmq
  template:
    metadata:
      labels:
        app: rabbitmq
    spec:
      initContainers:
      - name: "rabbitmq-config"
        image: busybox:1.32.0
        volumeMounts:
        - name: rabbitmq-config
          mountPath: /tmp/rabbitmq
        - name: rabbitmq-config-rw
          mountPath: /etc/rabbitmq
        command:
        - sh
        - -c
        - cp /tmp/rabbitmq/rabbitmq.conf /etc/rabbitmq/rabbitmq.conf && echo '' >> /etc/rabbitmq/rabbitmq.conf;
          cp /tmp/rabbitmq/enabled_plugins /etc/rabbitmq/enabled_plugins
      volumes:
      - name: rabbitmq-config
        configMap:
          name: rabbitmq-config
          optional: false
          items:
          - key: enabled_plugins
            path: "enabled_plugins"
          - key: rabbitmq.conf
            path: "rabbitmq.conf"
      - name: rabbitmq-config-rw
        emptyDir: {}
      serviceAccount: rabbitmq
      containers:
      - name: rabbitmq      
        image: rabbitmq:3.8.5
        imagePullPolicy: IfNotPresent
        resources:
          limits:
            cpu: 4
            memory: 2048Mi
          requests:
            cpu: 0.1
            memory: 128Mi
        ports:
            - name: epmd
              protocol: TCP
              containerPort: 4369
            - name: amqp
              protocol: TCP
              containerPort: 5672
            - name: http
              protocol: TCP
              containerPort: 15672
        readinessProbe:
          httpGet:
            path: /
            port: 15672
          initialDelaySeconds: 5
          periodSeconds: 15
          timeoutSeconds: 10
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              apiVersion: v1
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: RABBITMQ_NODENAME
          value: rabbit@$(POD_NAME).rabbitmq-svc.$(POD_NAMESPACE).svc.cluster.local
        - name: RABBITMQ_USE_LONGNAME
          value: "true"
        - name: RABBITMQ_DEFAULT_VHOST
          value: 'rabbitmq_vhost'
        - name: RABBITMQ_DEFAULT_USER
          value: admin
        - name: RABBITMQ_DEFAULT_PASS
          value: rabbitmq
        - name: RABBITMQ_LOGS
          value: /var/lib/rabbitmq/rabbitmq/rabbitmq.log
        - name: RABBITMQ_SASL_LOGS
          value: /var/lib/rabbitmq/rabbitmq/rabbitmq-sasl.log
        - name: TZ
          value: 'Asia/Shanghai'
        - name: RABBITMQ_ERLANG_COOKIE
          value: RABBITMQ-SECRET-KEY
        volumeMounts:
          - name: rabbitmq-config-rw
            mountPath: "/etc/rabbitmq"
          - name: mq-data
            mountPath: /var/lib/rabbitmq
      imagePullSecrets:
        - name: harbor-bbotte
  volumeClaimTemplates:
  - metadata:
      name: mq-data
    spec:
      accessModes: [ "ReadWriteMany" ]
      resources:
        requests:
          storage: 10Gi


```

---

最后配置rabbitmq的service

```
kind: Service
apiVersion: v1
metadata:
  name: rabbitmq-svc
  namespace: default
spec:
  type: NodePort
  selector:
    app: rabbitmq
  ports:
  - port: 5672
    name: mq5672
    targetPort: 5672
    nodePort: 32701
  - port: 15672
    name: mqweb
    targetPort: 15672
    nodePort: 30572
  - port: 4369
    name: epmd
    targetPort: 4369
  - port: 25672
    name: mq25672
    targetPort: 25672

```

这时候，3个mq的pod已经创建，那么让这3个pod成为一个集群，进入rabbitmq-1

```
kubectl exec -it rabbitmq-1 bash
rabbitmqctl stop_app ;rabbitmqctl join_cluster --disc rabbit@rabbitmq-0.rabbitmq-svc.default.svc.cluster.local ;rabbitmqctl start_app
```

进入rabbitmq-2，并配置ha策略

```
kubectl exec -it rabbitmq-2 bash
rabbitmqctl stop_app ;rabbitmqctl join_cluster --disc rabbit@rabbitmq-0.rabbitmq-svc.default.svc.cluster.local ;rabbitmqctl start_app
rabbitmqctl cluster_status

rabbitmqctl --erlang-cookie ${RABBITMQ_ERLANG_COOKIE} set_policy --vhost uclass_pd mq-ha "^" '{"ha-mode":"all","ha-sync-mode":"automatic"}'
```



last，删除rabbitmq集群：

```
kubectl delete -f rabbitmq-statefulset.yaml  还有 rbac，configmap的yaml
kubectl delete pvc/mq-data-rabbitmq-2
kubectl delete pvc/mq-data-rabbitmq-1
kubectl delete pvc/mq-data-rabbitmq-0
kubectl delete pv/pv-mq3
kubectl delete pv/pv-mq2
kubectl delete pv/pv-mq1

```

参考 [diy-kubernetes-examples](https://github.com/rabbitmq/diy-kubernetes-examples)

2021年01月11日 于 [linux工匠](https://bbotte.github.io/) 发表