---
layout: default
---

# 在kubernetes中部署skywalking(elasticsearch7集群)


根据skywalking不同版本，需要不同版本es集群，[es6集群部署](https://bbotte.github.io/service_config/kubernetes-install-elasticsearch-6-with-statefulset) ，这次使用elasticsearch7的集群作为skywalking的存储，pv的创建同样使用[在kubernetes中statefu方式安装elasticsearch-6集群](https://bbotte.github.io/service_config/kubernetes-install-elasticsearch-6-with-statefulset)步骤

下面是elasticsearch 7 rbac配置

---

设置RBAC

```
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: skywalking-sa-cluster

---
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata: 
  name: skywalking-sa-role
  namespace: default
rules:
- apiGroups: [""]
  resources: ["endpoints"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: skywalking-sa-role-binding
  namespace: default
subjects:
- kind: ServiceAccount
  name: skywalking-sa-cluster
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: skywalking-sa-role
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: skywalking-sa-cluster-role
rules:
  - apiGroups: [ "" ]
    resources:
      - "pods" # @feature: cluster; OAP needs to read other OAP Pods information to form a cluster
               # @feature: als; OAP needs to read Pods metadata to analyze the access logs
      - "services" # @feature: als; OAP needs to read services metadata to analyze the access logs
      - "endpoints" # @feature: als; OAP needs to read endpoints metadata to analyze the access logs
      - "nodes" # @feature: als; OAP needs to read nodes metadata to analyze the access logs
      - "configmaps"
    verbs: [ "get", "watch", "list" ]
  - apiGroups: [ "batch" ]
    resources:
      - "jobs" # @feature: cluster; OAP needs to wait for the init job to complete
    verbs: [ "get", "watch", "list" ]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: skywalking-sa-cluster-role-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: skywalking-sa-cluster-role
subjects:
  - kind: ServiceAccount
    name: skywalking-sa-cluster
    namespace: default

```

---

elasticsearch 7的参数配置，statefulset 部署配置

```
---
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
    processors: ${PROCESSORS:}
    gateway.expected_master_nodes: ${EXPECTED_MASTER_NODES:2}
    gateway.expected_data_nodes: ${EXPECTED_DATA_NODES:1}
    gateway.recover_after_time: ${RECOVER_AFTER_TIME:5m}
    gateway.recover_after_master_nodes: ${RECOVER_AFTER_MASTER_NODES:2}
    gateway.recover_after_data_nodes: ${RECOVER_AFTER_DATA_NODES:1}
    http.cors.enabled: true
    http.cors.allow-origin: "*"
    xpack.security.enabled: false
    ingest.geoip.downloader.enabled: false

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

---

kind: StatefulSet
apiVersion: apps/v1
metadata:
  name: elasticsearch
  namespace: default
spec:
  serviceName: es-svc
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      nodeSelector:
        deploytype: normal
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
      serviceAccount: skywalking-sa-cluster
      containers:
      - name: elasticsearch
        image: elasticsearch:7.16.2
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
          value: "-Djava.net.preferIPv4Stack=true -Xms1400m -Xmx1400m"
        - name: discovery.seed_hosts
          value: "elasticsearch-0.es-svc,elasticsearch-1.es-svc,elasticsearch-2.es-svc"
        - name: cluster.initial_master_nodes
          value: "elasticsearch-0,elasticsearch-1,elasticsearch-2 "
        volumeMounts:
          - name: es-data
            mountPath: /usr/share/elasticsearch/data
          - mountPath: /usr/share/elasticsearch/config/elasticsearch.yml
            name: config
            subPath: elasticsearch.yml
          - mountPath: /usr/share/elasticsearch/config/log4j2.properties
            name: log4j2
            subPath: log4j2.properties
      imagePullSecrets:
        - name: harbor-bbotte
      volumes:
      - name: config
        configMap:
          name: es-cm
      - name: log4j2
        configMap:
          name: es-cm
  volumeClaimTemplates:
  - metadata:
      name: es-data
    spec:
      accessModes: [ "ReadWriteMany" ]
      resources:
        requests:
          storage: 50Gi

---
kind: Service
apiVersion: v1
metadata:
  name: es-svc
  namespace: default
  labels:
    app: elasticsearch
spec:
  type: NodePort
  clusterIP: 172.30.8.248
  selector:
    app: elasticsearch
  ports:
  - port: 9200
    name: es9200
    targetPort: 9200
    nodePort: 30920
  - port: 9300
    name: es9300
    targetPort: 9300


```

注意这里es使用了clusterIP，是对es服务一个固定ip，因为skywalking要用。现在es集群已经部署完毕，查看es的接口确认服务是否正常，

```
curl -XGET 'http://localhost:9200/_cluster/stats?human&pretty'
```

---

最后部署skywalking，测试的时候倒是其中几个参数耽误挺长时间，比如SW_STORAGE是elasticsearch7，不是elasticsearch；SW_STORAGE_ES_CLUSTER_NODES的值是ip：port，不能是elasticsearch的服务名:port。初始化的job官方还有个探测es是否就绪的判断，这里省了。

```
apiVersion: v1
kind: Service
metadata:
  name: oap
spec:
  selector:
    app: skywalking
  ports:
    - name: metrics
      port: 1234
    - name: grpc
      port: 11800
    - name: http
      port: 12800

---
apiVersion: batch/v1
kind: Job
metadata:
  name: oap-init-job # @feature: cluster; set up an init job to initialize ES templates and indices
spec:
  template:
    metadata:
      name: oap-init-job
    spec:
      serviceAccountName: skywalking-sa-cluster
      restartPolicy: Never
      containers:
        - name: oap-init
          image: skywalking.docker.scarf.sh/apache/skywalking-oap-server:8.7.0-es7
          imagePullPolicy: IfNotPresent
          env: # @feature: cluster; make sure all env vars are the same with the cluster nodes as this will affect templates / indices
            - name: JAVA_OPTS
              value: "-Dmode=init " # @feature: cluster; set the OAP mode to "init" so the job can complete
            - name: SW_STORAGE
              value: elasticsearch7        #这里必须是6或者7，要加上
            - name: SW_STORAGE_ES_CLUSTER_NODES
              value: "172.30.8.248:9200"   #这里必须写ip，不能写es的服务名

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skywalking
  labels:
    app: skywalking
spec:
  replicas: 2 # @feature: cluster; set OAP replicas to >1
  selector:
    matchLabels:
      app: skywalking
  template:
    metadata:
      labels:
        app: skywalking
    spec:
      initContainers:
        - name: wait-for-oap-init
          image: bitnami/kubectl:1.20.12
          command:
            - 'kubectl'
            - 'wait'
            - '--for=condition=complete'
            - 'job/oap-init-job'
      serviceAccountName: skywalking-sa-cluster
      containers:
        - name: skywalking
          image: skywalking.docker.scarf.sh/apache/skywalking-oap-server:8.7.0-es7
          imagePullPolicy: IfNotPresent
          resources:
            limits:
              cpu: 4000m
              memory: "4096Mi"
            requests:
              cpu: 1000m
              memory: "1024Mi"
          ports:
            - name: metrics # @feature: so11y; set a name for the metrics port that can be referenced in otel config
              containerPort: 1234
            - name: grpc
              containerPort: 11800
            - name: http
              containerPort: 12800
          livenessProbe:
            tcpSocket:
              port: 12800
            initialDelaySeconds: 15
            periodSeconds: 20
          env:
            - name: JAVA_OPTS
              value: "-Dmode=no-init"
            - name: SW_CLUSTER
              value: kubernetes # @feature: cluster; set cluster coordinator to kubernetes
            - name: SW_CLUSTER_K8S_NAMESPACE
              value: default
            - name: SW_CLUSTER_K8S_LABEL
              value: "app=skywalking,release=skywalking,component=oap" # @feature: cluster; set label selectors to select OAP Pods as a cluster
            - name: SKYWALKING_COLLECTOR_UID
              valueFrom:
                fieldRef:
                  fieldPath: metadata.uid
            - name: SW_OTEL_RECEIVER
              value: default # @feature: so11y;vm;kubernetes-monitor enable OpenTelemetry receiver to receive OpenTelemetry metrics
            - name: SW_OTEL_RECEIVER_ENABLED_OC_RULES
              # @feature: vm; enable vm rules to analyze VM metrics
              # @feature: so11y; enable oap rules to analyze OAP metrics
              # @feature: kubernetes-monitor; enable rules to analyze Kubernetes Cluster/Node/Service metrics
              # @feature: istiod-monitor; enable rules to analyze Istio control plane metrics
              value: oap,k8s-cluster,k8s-node,k8s-service
            - name: SW_STORAGE
              value: elasticsearch7
            - name: SW_STORAGE_ES_CLUSTER_NODES
              value: "172.30.8.248:9200"       #这里必须写ip，不能写es的服务名，所以es中用了clusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skywalking-ui
  labels:
    app: skywalking-ui
spec:
  replicas: 1
  selector:
    matchLabels:
      app: skywalking-ui
  template:
    metadata:
      labels:
        app: skywalking-ui
    spec:
      affinity:
      containers:
      - name: skywalking-ui
        image: skywalking.docker.scarf.sh/apache/skywalking-ui:8.7.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8080
          name: page
        env:
        - name: SW_OAP_ADDRESS
          value: http://oap:12800
---
apiVersion: v1
kind: Service
metadata:
  name: skywalking-ui
  labels:
    app: skywalking-ui
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 8080
      protocol: TCP
      nodePort: 30080
  selector:
    app: skywalking-ui


```

安装skywalking遇到奇奇怪怪的错误，多是因为配置的问题，还有skywalking init缺少表的,先把deploy的skywalking no-init改为 init，删掉deploy，再apply deploy一次解决

```
table: meter_oap_instance_trace_latency_percentile does not exist. OAP is running in 'no-init' mode, waiting... retry 3s later

table: alarm_record does not exist. OAP is running in 'no-init' mode, waiting... retry 3s later

```

参考 
- [skywalking-showcase](https://github.com/apache/skywalking-showcase/tree/main/deploy/platform/kubernetes)
- [skywalking-kubernetes](https://github.com/apache/skywalking-kubernetes)

skywalking-kubernetes这里是helm的模板，可以导出为yaml配置，比如：

```
export SKYWALKING_RELEASE_NAME=skywalking

helm template "${SKYWALKING_RELEASE_NAME}" ./chart/skywalking/ --set ui.image.tag=8.8.1 --set oap.storageType=elasticsearch --set oap.image.tag=8.8.1 > skywalking.yaml
```

最后，业务客户端连skywalking的服务名为 oap:11800

2021年01月24日 于 [linux工匠](https://bbotte.github.io/) 发表