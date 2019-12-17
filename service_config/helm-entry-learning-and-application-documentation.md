---
layout: default
---

# helm入门学习及应用文档

helm是kubernetes配置的包管理器，相当于centos的rpm，Debian的apk。可以使用网上已配置的模板或自己制作的模板构建服务，并做服务的版本管理，发布、回滚等。先决条件为kubernetes集群已建立，版本大于1.6。chart、helm和tiller关系可以理解如下：

```
                 helm(舵轮)客户端
chart(航海图)   ---------------→    tiller(舵杆)服务端
配置、模板的包                     接受helm请求，kubernetes集群上运行
```

### 配置helm

helm主机

```
wget https://storage.googleapis.com/kubernetes-helm/helm-v2.10.0-linux-amd64.tar.gz
tar -xf helm-v2.10.0-linux-amd64.tar.gz 
mv linux-amd64/helm /usr/bin/
# helm version
Client: &version.Version{SemVer:"v2.10.0", GitCommit:"9ad53aac42165a5fadc6c87be0dea6b115f93090", GitTreeState:"clean"}
Server: &version.Version{SemVer:"v2.10.0", GitCommit:"9ad53aac42165a5fadc6c87be0dea6b115f93090", GitTreeState:"clean"}
 
# helm
The Kubernetes package manager
 
To begin working with Helm, run the 'helm init' command:
 
	$ helm init
 
This will install Tiller to your running Kubernetes cluster.
It will also set up any necessary local configuration.
 
Common actions from this point include:
 
- helm search:    search for charts
- helm fetch:     download a chart to your local directory to view
- helm install:   upload the chart to Kubernetes
- helm list:      list releases of charts
 
Environment:
  $HELM_HOME          set an alternative location for Helm files. By default, these are stored in ~/.helm
  $HELM_HOST          set an alternative Tiller host. The format is host:port
  $HELM_NO_PLUGINS    disable plugins. Set HELM_NO_PLUGINS=1 to disable plugins.
  $TILLER_NAMESPACE   set an alternative Tiller namespace (default "kube-system")
  $KUBECONFIG         set an alternative Kubernetes configuration file (default "~/.kube/config")
 
Usage:
  helm [command]
 
Available Commands:
  completion  Generate autocompletions script for the specified shell (bash or zsh)
  create      create a new chart with the given name
  delete      given a release name, delete the release from Kubernetes
  dependency  manage a chart's dependencies
  fetch       download a chart from a repository and (optionally) unpack it in local directory
  get         download a named release
  history     fetch release history
  home        displays the location of HELM_HOME
  init        initialize Helm on both client and server
  inspect     inspect a chart
  install     install a chart archive
  lint        examines a chart for possible issues
  list        list releases
  package     package a chart directory into a chart archive
  plugin      add, list, or remove Helm plugins
  repo        add, list, remove, update, and index chart repositories
  reset       uninstalls Tiller from a cluster
  rollback    roll back a release to a previous revision
  search      search for a keyword in charts
  serve       start a local http web server
  status      displays the status of the named release
  template    locally render templates
  test        test a release
  upgrade     upgrade a release
  verify      verify that a chart at the given path has been signed and is valid
  version     print the client/server version information
 
Flags:
      --debug                           enable verbose output
  -h, --help                            help for helm
      --home string                     location of your Helm config. Overrides $HELM_HOME (default "/root/.helm")
      --host string                     address of Tiller. Overrides $HELM_HOST
      --kube-context string             name of the kubeconfig context to use
      --kubeconfig string               absolute path to the kubeconfig file to use
      --tiller-connection-timeout int   the duration (in seconds) Helm will wait to establish a connection to tiller (default 300)
      --tiller-namespace string         namespace of Tiller (default "kube-system")
 
# mkdir .kube
```

把kubernetes集群 master的.kube/config配置文件复制到helm主机的/root/.kube/目录，因为helm需要通过此配置和kubernetes通信

```
chown 600 .kube/config
```

### 初始化helm

```
# helm init --service-account tiller
Creating /root/.helm 
Creating /root/.helm/repository 
Creating /root/.helm/repository/cache 
Creating /root/.helm/repository/local 
Creating /root/.helm/plugins 
Creating /root/.helm/starters 
Creating /root/.helm/cache/archive 
Creating /root/.helm/repository/repositories.yaml 
Adding stable repo with URL: https://kubernetes-charts.storage.googleapis.com 
Adding local repo with URL: http://127.0.0.1:8879/charts 
$HELM_HOME has been configured at /root/.helm.
 
Tiller (the Helm server-side component) has been installed into your Kubernetes Cluster.
 
Please note: by default, Tiller is deployed with an insecure 'allow unauthenticated users' policy.
To prevent this, run `helm init` with the --tiller-tls-verify flag.
For more information on securing your installation see: https://docs.helm.sh/using_helm/#securing-your-helm-installation
Happy Helming!
```

### tiller配置

k8s master主机

```
# kubectl config current-context
kubernetes-admin@kubernetes
# cat helm-rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tiller
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: tiller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: tiller
    namespace: kube-system
 
# kubectl create -f helm-rbac.yaml
# kubectl create namespace tiller
namespace "tiller" created
# kubectl create serviceaccount tiller --namespace tiller
serviceaccount "tiller" created
# cat tiller-role.yaml
kind: Role
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: tiller-manager
  namespace: tiller
rules:
- apiGroups: ["", "batch", "extensions", "apps"]
  resources: ["*"]
  verbs: ["*"]
 
# kubectl create -f tiller-role.yaml
role "tiller-manager" created
# cat rolebinding-tiller.yaml
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: tiller-binding
  namespace: tiller
subjects:
- kind: ServiceAccount
  name: tiller
  namespace: tiller
roleRef:
  kind: Role
  name: tiller-manager
  apiGroup: rbac.authorization.k8s.io
 
# kubectl create -f rolebinding-tiller.yaml
rolebinding "tiller-binding" created
# kubectl get po -n tiller -o wide
NAME                             READY     STATUS             RESTARTS   AGE       IP             NODE
tiller-deploy-5d55598846-9rkpz   0/1       ImagePullBackOff   0          1m        10.244.6.161   k8snode03
```

node3节点导入helm的镜像，需要翻过去，gcr.io/kubernetes-helm/tiller:v2.10.0

tiller度娘网盘链接: https://pan.baidu.com/s/1Uyt099mUGD7QdNvjO-QBag 密码: uv98

```
# kubectl get po -n tiller -o wide
NAME                             READY     STATUS    RESTARTS   AGE       IP             NODE
tiller-deploy-5d55598846-9rkpz   0/1       Running   0          6m        10.244.6.161   k8snode03
```

### 使用helm创建服务

helm主机

```
# helm init --service-account tiller --tiller-namespace tiller
$HELM_HOME has been configured at /root/.helm.
 
Tiller (the Helm server-side component) has been installed into your Kubernetes Cluster.
 
Please note: by default, Tiller is deployed with an insecure 'allow unauthenticated users' policy.
To prevent this, run `helm init` with the --tiller-tls-verify flag.
For more information on securing your installation see: https://docs.helm.sh/using_helm/#securing-your-helm-installation
Happy Helming!
 
# helm repo update
Hang tight while we grab the latest from your chart repositories...
...Skip local chart repository
...Successfully got an update from the "stable" chart repository
Update Complete. ⎈ Happy Helming!⎈
```

```
# helm install stable/nginx-ingress
NAME:   cloying-abalone
LAST DEPLOYED: Fri Sep  7 10:36:40 2018
NAMESPACE: default
STATUS: DEPLOYED
 
RESOURCES:
==> v1beta1/Role
NAME                           AGE
cloying-abalone-nginx-ingress  0s
 
==> v1/Pod(related)
NAME                                                            READY  STATUS             RESTARTS  AGE
cloying-abalone-nginx-ingress-controller-5cf799f7f4-lbngf       0/1    ContainerCreating  0         0s
cloying-abalone-nginx-ingress-default-backend-799c75f954-ss7wr  0/1    ContainerCreating  0         0s
 
==> v1/ConfigMap
NAME                                      DATA  AGE
cloying-abalone-nginx-ingress-controller  1     0s
 
==> v1/ServiceAccount
NAME                           SECRETS  AGE
cloying-abalone-nginx-ingress  1        0s
 
==> v1beta1/ClusterRole
NAME                           AGE
cloying-abalone-nginx-ingress  0s
 
==> v1beta1/ClusterRoleBinding
NAME                           AGE
cloying-abalone-nginx-ingress  0s
 
==> v1beta1/RoleBinding
NAME                           AGE
cloying-abalone-nginx-ingress  0s
 
==> v1/Service
NAME                                           TYPE          CLUSTER-IP      EXTERNAL-IP  PORT(S)                     AGE
cloying-abalone-nginx-ingress-controller       LoadBalancer  10.110.25.124   <pending>    80:30876/TCP,443:30543/TCP  0s
cloying-abalone-nginx-ingress-default-backend  ClusterIP     10.108.215.121  <none>       80/TCP                      0s
 
==> v1beta1/Deployment
NAME                                           DESIRED  CURRENT  UP-TO-DATE  AVAILABLE  AGE
cloying-abalone-nginx-ingress-controller       1        1        1           0          0s
cloying-abalone-nginx-ingress-default-backend  1        1        1           0          0s
 
 
NOTES:
The nginx-ingress controller has been installed.
It may take a few minutes for the LoadBalancer IP to be available.
You can watch the status by running 'kubectl --namespace default get services -o wide -w cloying-abalone-nginx-ingress-controller'
 
An example Ingress that makes use of the controller:
 
  apiVersion: extensions/v1beta1
  kind: Ingress
  metadata:
    annotations:
      kubernetes.io/ingress.class: nginx
    name: example
    namespace: foo
  spec:
    rules:
      - host: www.example.com
        http:
          paths:
            - backend:
                serviceName: exampleService
                servicePort: 80
              path: /
    # This section is only required if TLS is to be enabled for the Ingress
    tls:
        - hosts:
            - www.example.com
          secretName: example-tls
 
If TLS is enabled for the Ingress, a Secret containing the certificate and key must also be provided:
 
  apiVersion: v1
  kind: Secret
  metadata:
    name: example-tls
    namespace: foo
  data:
    tls.crt: <base64 encoded cert>
    tls.key: <base64 encoded key>
  type: kubernetes.io/tls
```

因为拉取不到镜像会失败，需要翻过去的镜像：
k8s.gcr.io/defaultbackend:1.4

defaultbackend度娘网盘链接: https://pan.baidu.com/s/1OKGAJdU-kktGPkHYE8LF_g 密码: tt7c
nginx镜像，不用翻过去
quay.io/kubernetes-ingress-controller/nginx-ingress-controller:0.19.0

kubernetes master节点查看状态

```
# kubectl get po -o wide
NAME                                                             READY     STATUS    RESTARTS   AGE       IP             NODE
cloying-abalone-nginx-ingress-controller-5cf799f7f4-lbngf        1/1       Running   0          8m        10.244.5.146   k8snode02
cloying-abalone-nginx-ingress-default-backend-799c75f954-ss7wr   1/1       Running   0          8m        10.244.5.149   k8snode02
```

helm主机查看，删除

```
# helm list
NAME           	REVISION	UPDATED                 	STATUS  	CHART               	APP VERSION	NAMESPACE
cloying-abalone	1       	Fri Sep  7 10:36:40 2018	DEPLOYED	nginx-ingress-0.28.2	0.19.0     	default  
# helm delete cloying-abalone
release "cloying-abalone" deleted
```

此nginx服务的仓库链接
<https://hub.kubeapps.com/charts/stable/nginx-ingress>
github链接
<https://github.com/kubernetes/ingress-nginx>
主机上helm拉取的nginx服务配置

```
vim .helm/cache/archive/nginx-ingress-0.28.2.tgz
```

[helm文档](https://docs.helm.sh/)

### 创建项目

使用helm创建一个项目，名字为bbotte

```
# helm create bbotte
Creating bbotte
# tree bbotte/
bbotte/
├── charts
├── Chart.yaml
├── templates
│   ├── deployment.yaml
│   ├── _helpers.tpl
│   ├── ingress.yaml
│   ├── NOTES.txt
│   └── service.yaml
└── values.yaml
```

修改配置,镜像改为自己的

```
# vim bbotte/values.yaml
 
replicaCount: 1
 
image:
  repository: harbor.bbotte.com/devops/nginx
  tag: 0.6
  pullPolicy: IfNotPresent
 
nameOverride: ""
fullnameOverride: ""
 
service:
  type: ClusterIP
  port: 80
 
ingress:
  enabled: true
  annotations:
    kubernetes.io/ingress.class: traefik
    # kubernetes.io/ingress.class: nginx
    # kubernetes.io/tls-acme: "true"
  path: /
  hosts:
    - chart-example.local
  tls: []
  #  - secretName: chart-example-tls
  #    hosts:
  #      - chart-example.local
```

### helm打包

```
# helm package bbotte/
Successfully packaged chart and saved it to: /root/bbotte-0.1.0.tgz
# helm search bbotte
NAME        	CHART VERSION	APP VERSION	DESCRIPTION                
local/bbotte	0.1.0        	1.0        	A Helm chart for Kubernetes
```

### 发布应用

```
# helm install --name bbotte local/bbotte
Error: failed to download "local/bbotte" (hint: running `helm repo update` may help)
[root@matuoyi ~]# helm repo update
Hang tight while we grab the latest from your chart repositories...
...Skip local chart repository
...Successfully got an update from the "stable" chart repository
Update Complete. ⎈ Happy Helming!⎈
```

本地启动helm服务，监听在8879端口，这样才可以创建

```
# nohup helm serve &
```

```
# helm install --name bbotte local/bbotte
NAME:   bbotte
LAST DEPLOYED: Fri Sep  7 16:36:29 2018
NAMESPACE: default
STATUS: DEPLOYED
 
RESOURCES:
==> v1/Service
NAME    TYPE       CLUSTER-IP    EXTERNAL-IP  PORT(S)  AGE
bbotte  ClusterIP  10.96.14.194  <none>       80/TCP   0s
 
==> v1beta2/Deployment
NAME    DESIRED  CURRENT  UP-TO-DATE  AVAILABLE  AGE
bbotte  1        0        0           0          0s
 
==> v1beta1/Ingress
NAME    HOSTS                ADDRESS  PORTS  AGE
bbotte  chart-example.local  80       0s
 
==> v1/Pod(related)
NAME                     READY  STATUS   RESTARTS  AGE
bbotte-7cc5864599-w6gr6  0/1    Pending  0         0s
 
 
NOTES:
1. Get the application URL by running these commands:
  http://chart-example.local/
 
# helm status bbotte
LAST DEPLOYED: Fri Sep  7 16:36:29 2018
NAMESPACE: default
STATUS: DEPLOYED
 
RESOURCES:
==> v1/Service
NAME    TYPE       CLUSTER-IP    EXTERNAL-IP  PORT(S)  AGE
bbotte  ClusterIP  10.96.14.194  <none>       80/TCP   1m
 
==> v1beta2/Deployment
NAME    DESIRED  CURRENT  UP-TO-DATE  AVAILABLE  AGE
bbotte  1        1        1           1          1m
 
==> v1beta1/Ingress
NAME    HOSTS                ADDRESS  PORTS  AGE
bbotte  chart-example.local  80       1m
 
==> v1/Pod(related)
NAME                     READY  STATUS   RESTARTS  AGE
bbotte-7cc5864599-w6gr6  1/1    Running  0         1m
```

彻底删除这个部署

```
# helm del --purge bbotte
release "bbotte" deleted
```

look一下自己的仓库

```
curl 127.0.0.1:8879
```

另：自己制作helm项目太麻烦，<https://hub.kubeapps.com/> 这个网站里面这么多已制作好的helm项目，怎么直接使用呢，添加kubeapps的仓库即可，比如安装nginx-ingress，链接为：https://hub.kubeapps.com/charts/stable/nginx-ingress

```
helm repo add bitnami https://charts.bitnami.com/bitnami
 
helm install stable/nginx-ingress
```

2018年09月07日 于 [linux工匠](http://www.bbotte.com/) 发表