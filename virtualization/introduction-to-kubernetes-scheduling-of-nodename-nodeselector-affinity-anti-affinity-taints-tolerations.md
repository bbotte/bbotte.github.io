# kubernetes的调度简介nodeName nodeSelector Affinity Anti-affinity Taints Tolerations

1.nodeName和nodeSelector
2.亲和Affinity和反亲和anti-affinity

1. nodeAffinity
2. 再举个例子
3. podAffinity和podAntiAffinity

3.taints污点和tolerations容忍
4.参考文档

kubernetes的调度简介nodeName nodeSelector Affinity Anti-affinity Taints Tolerations

kubernetes集群调度是pod节点之间、pod和node节点之间的互动关系，为满足线上pod和pod间，pod和node节点间结合或互斥关系，有单节点、多节点(打tag),硬性要求,弹性要求、权重等选项。下面按3块来说明：
**nodeName和nodeSelector节点选择器**
**Affinity****亲和和anti-affinity反亲和**
**taints污点和tolerations容忍**

### nodeName和nodeSelector

目的是给pod选择指定的node来调度

```
kubectl explain pod.spec.nodeName
kubectl explain pod.spec.nodeSelector
```

nodeName只能选择一个node主机运行pod服务，如下，只能调度到k8snode1节点

```
pods/pod-nginx.yaml  
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    env: test
spec:
  containers:
  - name: nginx
    image: nginx
    imagePullPolicy: IfNotPresent
  nodeName: k8snode1
```

nodeSelector，选择打标签的一批node主机运行pod服务，官网例子如下

```
kubectl label nodes k8snode1 disktype=ssd
 
pods/pod-nginx.yaml  
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    env: test
spec:
  containers:
  - name: nginx
    image: nginx
    imagePullPolicy: IfNotPresent
  nodeSelector:
    disktype: ssd
```

对k8snode1节点加了标签，disktype=ssd，nginx需要调度到有这个标签的node节点上

### 亲和Affinity和反亲和anti-affinity

增强版节点选择器亲和Affinity和反亲和anti-affinity，更详细配置了pod可以调度到哪些node节点上，目的是给pod选择可运行的node节点，并且用以定义pod之间互斥和相依关系

```
kubectl explain pod.spec.affinity.nodeAffinity
kubectl explain pod.spec.affinity.podAffinity
kubectl explain pod.spec.affinity.podAntiAffinity
```

requiredDuringSchedulingIgnoredDuringExecution 硬性要求
preferredDuringSchedulingIgnoredDuringExecution 弹性要求

#### **nodeAffinity**

官网例子如下

```
pods/pod-with-node-affinity.yaml  
apiVersion: v1
kind: Pod
metadata:
  name: with-node-affinity
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: e2e-az-name
            operator: In
            values:
            - e2e-az1
            - e2e-az2
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 1
        preference:
          matchExpressions:
          - key: another-node-label-key
            operator: In
            values:
            - another-node-label-value
  containers:
  - name: with-node-affinity
    image: k8s.gcr.io/pause:2.0
```

上面例子是说这个pod只能部署到key是e2e-az-name，value是e2e-az1或e2e-az2主机上，最好是有这样的标签：key是another-node-label-key，value是another-node-label-value，此类主机优先
operator可以为In, NotIn, Exists, DoesNotExist, Gt, Lt，不同的值，结果也不相同，见 kubectl explain pod.spec.affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms.matchExpressions.operator
如果pod调度完成，再修改上面参数，那么此pod也不会被重新调度
weight数值越大，权重越高
为了部署上面pod，需要对其中一个node节点打标签，否则pod是pending状态

```
kubectl label nodes k8snode1 e2e-az-name=e2e-az1
```

#### 再举个例子：

```
kind: Deployment
apiVersion: apps/v1
metadata:
  name:  bbotte-nodeaffi
spec:
  replicas: 3
  revisionHistoryLimit: 1
  minReadySeconds: 20
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      k8s-app: bbotte-nodeaffi
  template:
    metadata:
      labels:
        k8s-app: bbotte-nodeaffi
    spec:
      containers:
      - name: bbotte
        image: nginx:latest
      imagePullSecrets:
        - name: default-secret
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values:
                 - 192.168.1.100
```

#### **podAffinity和podAntiAffinity**

redis配置示例如下

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-cache
spec:
  selector:
    matchLabels:
      app: store
  replicas: 3
  template:
    metadata:
      labels:
        app: store
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - store
            topologyKey: "kubernetes.io/hostname"
      containers:
      - name: redis-server
        image: redis:3.2-alpine
```

web-server配置示例如下

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
spec:
  selector:
    matchLabels:
      app: web-store
  replicas: 3
  template:
    metadata:
      labels:
        app: web-store
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - web-store
            topologyKey: "kubernetes.io/hostname"
        podAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - store
            topologyKey: "kubernetes.io/hostname"
      containers:
      - name: web-app
        image: nginx:1.12-alpine
```

上述配置用了PodAntiAffinity，规则为topologyKey: “kubernetes.io/hostname”。redis需要3个pod在3台不同的主机上保证高可用，所以用反亲和。各种集群，比如zookeeper，kafka也需要用到反亲和，避免集群所有pod调度到同一台node节点。而web-server也保证一个node节点只运行一个pod，标签为app:web-store，并且web-server和redis部署到同一个node节点

再举个例子

```
kind: Deployment
apiVersion: apps/v1
metadata:
  name: bbotte
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: bbotte
  template:
    metadata:
      labels:
        app: bbotte
    spec:
      containers:
        - name: bbotte
          image: 'nginx:v1'
          imagePullPolicy: IfNotPresent
      restartPolicy: Always
      dnsPolicy: ClusterFirst
      imagePullSecrets:
        - name: default-secret
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
           - labelSelector:
               matchExpressions:
                - key: app
                  operator: In
                  values:
                   - bbotte
             topologyKey: kubernetes.io/hostname
      schedulerName: default-scheduler
```

### taints污点和tolerations容忍

```
kubectl explain node.spec.taints
kubectl explain pods.spec.tolerations
```

taints和tolerations本质也是打了一个tag，类似于亲和性和反亲和(pod和pod之间的关系)，目的是node可以拒绝pod调度到自己上面。比如一个node节点给自己加了一个taints污点，pod必须能够tolerations容忍这个污点，才可以调度到这个node上面，忍一时风平浪静，退一步海阔天空，有污点就忍忍吧
查看master节点taints，是不允许pod调度到上面，

```
# kubectl describe node k8smaster01|grep -A 2 Annotations
Annotations:        node.alpha.kubernetes.io/ttl=0
                    volumes.kubernetes.io/controller-managed-attach-detach=true
Taints:             node-role.kubernetes.io/master:NoSchedule
```

那我偏要调度到master节点呢，比如coredns、kube-dns等，看看coredns

```
# kubectl describe po coredns-65dcdb4cf-5kwgj -n kube-system|grep -A 3 Tolerations
Tolerations:     CriticalAddonsOnly
                 node-role.kubernetes.io/master:NoSchedule
                 node.kubernetes.io/not-ready:NoExecute for 300s
                 node.kubernetes.io/unreachable:NoExecute for 300s
```

还是以coredns和kube-dns举例

```
https://raw.githubusercontent.com/cloudnativelabs/kube-router/master/daemonset/kubeadm-kuberouter-all-features.yaml
      tolerations:
      - key: CriticalAddonsOnly
        operator: Exists
      - effect: NoSchedule
        key: node-role.kubernetes.io/master
        operator: Exists
```

```
https://github.com/kubernetes/kubernetes/blob/master/cluster/addons/dns/kube-dns/kube-dns.yaml.sed
      tolerations:
      - key: "CriticalAddonsOnly"
        operator: "Exists"
```

有污点的话，添加容忍就可以调度。kubernetes的调度介绍以上几种方式，详细请阅览官方文档

### 参考文档

<https://kubernetes.io/docs/concepts/configuration/assign-pod-node/>

<https://kubernetes.io/docs/concepts/configuration/taint-and-toleration/>

<https://github.com/kubernetes/community/blob/master/contributors/design-proposals/scheduling/nodeaffinity.md>

<https://github.com/kubernetes/community/blob/master/contributors/design-proposals/scheduling/podaffinity.md>

2018年09月12日 于 [linux工匠](http://www.bbotte.com/) 发表