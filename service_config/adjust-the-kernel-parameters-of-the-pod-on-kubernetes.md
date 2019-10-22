# kubernetes调整pod的内核参数

经常遇到需要修改 kubernetes pod 中的内核参数，比如 sysctl 中 net.core.somaxconn，还有redis、MongoDB的transparent_hugepage。如果在 Dockerfile 中定义或者更改了这些参数，服务启动后，也是不生效的。如果用下面这种方式

```
docker run -it image_name:version /bin/bash
/ # sysctl -w net.core.somaxconn=8192
sysctl: error setting key 'net.core.somaxconn': Read-only file system
 
# docker run -it --privileged image_name:version /bin/bash
/ # sysctl -w net.core.somaxconn=8192
net.core.somaxconn = 8192
```

还是不能更改，docker文档中提到需用特权模式运行，对于kubernetes来说也是需要的，下面先介绍一个简便的方法，再说明一种麻烦的方式来解决问题

以redis来说，直接上例子，pod模式：

```
apiVersion: v1
kind: Pod
metadata:
  name: master-redis
  labels:
    name: master-redis
spec:
  initContainers:
  - name: disable-thp
    image: harbor.bbotte.com/devops/busybox
    command: ['/bin/sh','-c','echo never > /sys/kernel/mm/transparent_hugepage/enabled && sysctl -w net.core.somaxconn=65535 && sleep 1']
    imagePullPolicy: IfNotPresent
    securityContext:
      privileged: true
    volumeMounts:
    - mountPath: /sys
      name: mastersys
      readOnly: false
  containers:
    - name: master-redis
      image: harbor.bbotte.com/devops/redis:v0.01
      env:
      - name: DATADIR
        value: /data/masterredis
      ports:
        - containerPort: 6379
      resources:
        limits:
          cpu: "0.1"
          memory: 1024Mi
      volumeMounts:
        - name: redis-master-data
          mountPath: /data
  imagePullSecrets:
    - name: harbor-auth
  volumes:
    - name: redis-master-data
      persistentVolumeClaim:
        claimName: masterbranchgfs
    - name: mastersys
      hostPath:
        path: /sys
---
apiVersion: v1
kind: Service
metadata:
  name: master-redis-com
  labels:
    name: master-redis
spec:
  ports:
    - port: 6379
      targetPort: 6379
      protocol: TCP
  selector:
    name: master-redis
```

deployment模式：

```
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: master-redis
  labels:
    name: master-redis
spec:
  replicas: 1
  revisionHistoryLimit: 1
  minReadySeconds: 10
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      k8s-app: master-redis
  template:
    metadata:
      labels:
        k8s-app: master-redis
    spec:
      initContainers:
      - name: disable-thp
        image: harbor.bbotte.com/devops/busybox
        command: ['/bin/sh','-c','echo never > /sys/kernel/mm/transparent_hugepage/enabled && sysctl -w net.core.somaxconn=65535 && sleep 1']
        imagePullPolicy: IfNotPresent
        securityContext:
          privileged: true
        volumeMounts:
        - mountPath: /sys
          name: sys
          readOnly: false
      containers:
      - name: master-redis
        image: harbor.bbotte.com/devops/redis:v0.01
        imagePullPolicy: IfNotPresent
        env:
        - name: DATADIR
          value: /data/masterredis
        ports:
          - containerPort: 6379
        resources:
          limits:
            cpu: "0.1"
            memory: 1024Mi
        volumeMounts:
          - mountPath: /data
            name: redis-data-dir
      imagePullSecrets:
        - name: harbor-auth
      volumes:
      - name: redis-data-dir
        persistentVolumeClaim:
          claimName: masterbranchgfs
      - name: sys
        hostPath:
          path: /sys
```

上述配置文件见GitHub <https://github.com/bbotte/Commonly-Dockerfile>

更改透明大页transparent_hugepage，其实把系统的参数给更改了，上述加了 initContainers 对镜像做初始化的参数调整，然后运行镜像中服务，可以查看官方文档

<https://kubernetes.io/docs/concepts/workloads/pods/init-containers/>

<https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-initialization/>

![example](../images/2018/07/t0170a427f5e715c96a.gif)

```
---
apiVersion: v1
kind: ReplicationController
metadata:
  name: nginx-ingress-controller
  labels:
    k8s-app: nginx-ingress-lb
spec:
  replicas: 1
  selector:
    k8s-app: nginx-ingress-lb
  template:
    metadata:
      labels:
        k8s-app: nginx-ingress-lb
        name: nginx-ingress-lb
    spec:
      terminationGracePeriodSeconds: 60
      containers:
      - image: alpine:3.4
        name: sysctl-buddy
        # using kubectl exec you can check which other parameters is possible to change
        # IPC Namespace:     kernel.msgmax, kernel.msgmnb, kernel.msgmni, kernel.sem, kernel.shmall,
        #                    kernel.shmmax, kernel.shmmni, kernel.shm_rmid_forced and Sysctls
        #                    beginning with fs.mqueue.*
        # Network Namespace: Sysctls beginning with net.*
        #
        # kubectl <podname> -c sysctl-buddy -- sysctl -A | grep net
        command:
        - /bin/sh
        - -c
        - |
          while true; do
            sysctl -w net.core.somaxconn=32768
            sysctl -w net.ipv4.ip_local_port_range='1024 65535'
            sleep 10
          done
        imagePullPolicy: IfNotPresent
        securityContext:
          privileged: true
      - image: k8s.gcr.io/nginx-ingress-controller:0.8.3
        name: nginx-ingress-lb
        imagePullPolicy: Always
        readinessProbe:
          httpGet:
            path: /healthz
            port: 10254
            scheme: HTTP
        livenessProbe:
          httpGet:
            path: /healthz
            port: 10254
            scheme: HTTP
          initialDelaySeconds: 10
          timeoutSeconds: 1
        # use downward API
        env:
          - name: POD_NAME
            valueFrom:
              fieldRef:
                fieldPath: metadata.name
          - name: POD_NAMESPACE
            valueFrom:
              fieldRef:
                fieldPath: metadata.namespace
        ports:
        - containerPort: 80
          hostPort: 80
        - containerPort: 443
          hostPort: 443
        # we expose 8080 to access nginx stats in url /nginx-status
        # this is optional
        - containerPort: 8080
          hostPort: 8080
        args:
        - /nginx-ingress-controller
        - --default-backend-service=$(POD_NAMESPACE)/default-http-backend
```

上面这种方式都用了2个镜像，更改初始的镜像内核参数，来达到更改运行image的目的

 另一种复杂的方式更改docker kernel 的 sysctl 参数，

修改kubelet配置，可以修改系统参数

```
sed -i '9 aEnvironment="KUBELET_EXTRA_ARGS=--experimental-allowed-unsafe-sysctls=net.core.somaxconn"' /etc/systemd/system/kubelet.service.d/10-kubeadm.conf
systemctl daemon-reload
systemctl restart kubelet
```

即kubelet.service.d/10-kubeadm.conf文件增加了一行

```
Environment="KUBELET_CERTIFICATE_ARGS=--rotate-certificates=true --cert-dir=/var/lib/kubelet/pki"
Environment="KUBELET_EXTRA_ARGS=--experimental-allowed-unsafe-sysctls=net.core.somaxconn"  #增加
ExecStart=
ExecStart=/usr/bin/kubelet $KUBELET_KUBECONFIG_ARGS $KUBELET_SYSTEM_PODS_ARGS $KUBELET_NETWORK_ARGS $KUBELET_DNS_ARGS $KUBELET_AUTHZ_ARGS $KUBELET_CADVISOR_ARGS $KUBELET_CGROUP_ARGS $KUBELET_CERTIFICATE_ARGS $KUBELET_EXTRA_ARGS
```

举个例子：

```
apiVersion: v1
kind: Pod
metadata:
  name: dev-redis
  labels:
    name: dev-redis
  annotations:
    security.alpha.kubernetes.io/unsafe-sysctls: net.core.somaxconn=65535
spec:
  containers:
    - name: dev-redis
      image: harbor.bbotte.com/dev/redis-dev:v0.01
      securityContext:
        privileged: true
      ports:
        - containerPort: 6379
      resources:
        limits:
          cpu: "0.1"
          memory: 1024Mi
      volumeMounts:
        - mountPath: /data
          name: data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: gfsdata
```

也是用到了特权模式，不过这种方式只能修改 kernel sysctl 参数，其他参数不能修改，比如透明大页transparent_hugepage，有一定的局限性，线上根据自身配置更改就好。

2018年07月06日 于 [linux工匠](http://www.bbotte.com/) 发表

