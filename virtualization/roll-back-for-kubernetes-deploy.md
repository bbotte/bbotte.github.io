---
layout: default
---

# kubernetes服务的版本回退

下面简单说一下kubernetes的版本回退，因为已经在线上使用挺久的时间了，是利用kubernetes deployment的rollout histrory回退到指定版本，这篇是在[jinja和jenkins结合做为kubernetes的服务发布平台](http://bbotte.com/server-config/jinja-and-jenkins-as-service-delivery-platforms-for-kubernetes/)基础之上做的回滚，当然可以单独浏览

先给deployment打个样，webservice服务配置如下：

```
kind: Deployment
apiVersion: apps/v1beta2
metadata:
  name: pre-webservice
  labels:
    k8s-app: pre-webservice
  annotations:
    kubernetes.io/change-cause: pre-201806291944-216d6afd
spec:
  replicas: 1
  revisionHistoryLimit: 5
  minReadySeconds: 10
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      k8s-app: pre-webservice
  template:
    metadata:
      labels:
        k8s-app: pre-webservice
    spec:
      containers:
      - name: pre-webservice
        image: harbor.bbotte.com/service/webservice:pre-201806291944-216d6afd
        imagePullPolicy: IfNotPresent
        resources:
          limits:
            memory: 2048Mi
        ports:
        - containerPort: 9080
        livenessProbe:
          tcpSocket:
            port: 9080
          initialDelaySeconds: 15
          periodSeconds: 20
        volumeMounts:
          - name: pre-webservice-data-storage
            mountPath: /opt
      imagePullSecrets:
        - name: harbor-auth
      volumes:
      - name: pre-webservice-data-storage
        persistentVolumeClaim:
          claimName: gfs
 
---
kind: Service
apiVersion: v1
metadata:
  name: pre-webservice-com
  labels:
    k8s-app: pre-webservice
spec:
  selector:
    k8s-app: pre-webservice
  ports:
  - port: 9080
    targetPort: 9080
```

revisionHistoryLimit控制保留几个版本信息。版本回退即把服务回滚回去，镜像的版本号为： gitlab分支-时间戳-git_commit_short

kubernetes.io/change-cause 信息为docker的版本号，以免不知道kubernetes发布的版本和镜像之间的关系，即images 最后面一段，这个是有模板创建的 yaml 配置文件，

部署的命令，需要加 –record=false

```
kubectl apply -f webservice.yaml --record=false
```

查看已发布的版本信息：

```
kubectl rollout history deploy/pre-webservice
deployments "pre-webservice"
REVISION  CHANGE-CAUSE
55        pre-201806281524-57a710e1
56        pre-201806281555-403c38aa
57        pre-201806281601-166ffb31
58        pre-201806291944-216d6afd
```

前面是k8s保留的版本号，后面是docker-image的版本号

回滚到指定版本，因为版本号是以gitlab分支-时间戳-git_commit_short命名，所以可以依据gitlab提交的版本或者时间来回退

```
kubectl rollout undo daemonset/webservice --to-revision=56
```

这样就回退到56的版本

2018年07月01日 于 [linux工匠](https://bbotte.github.io/) 发表











