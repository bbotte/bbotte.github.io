---
layout: default
---

# kubeadm创建的kubernetes集群证书到期后续期

1.编译kubeadm
2.当前配置

1. 当前状态
2. 更换kubeadm

3.更改配置

1. kubelet配置和kube-controller-manager配置更改
2. 添加ClusterRoleBinding绑定
3. 查看当前系统配置

4.更新证书

1. 重新初始化kubernetes集群
2. master节点查看更新后证书
3. node节点操作
4. 在master查看node节点状态

5.设计理论

1. kubelet服务证书引导和自动更新过程说明
2. kubelet启动步骤
3. 证书到期的启动步骤

6.实际过程

1. 启用客户端证书轮换
2. 理解证书轮换配置

7.详细过程

1. kubeadm与kubelet更新证书过程
2. 证书自动续期
3. 参考

生产环境请用编译后更改证书时间的kubeadm初始化集群，下面文章生产环境没有验证，只是测试

## 编译kubeadm

```
# wget https://dl.google.com/go/go1.11.5.linux-amd64.tar.gz
# tar -C /usr/local -xzf go1.11.5.linux-amd64.tar.gz
# export PATH=$PATH:/usr/local/go/bin
# go get -d k8s.io/kubernetes  #下载kubernetes源码，500多M
# cd go/src/k8s.io/kubernetes/ #进入kubernetes源码目录
# git branch                 #查看当前分支
* master
# git tag -l                 #查看所有分支
# git checkout v1.9.4        #切换到指定分支
HEAD is now at bee2d15... Merge pull request #61045 from liggitt/subpath-1.9
# git branch
* (detached from v1.9.4)
  master
# vim vendor/k8s.io/client-go/util/cert/cert.go  #修改107行、152行
107                 NotAfter:     time.Now().Add(duration365d * 10).UTC(),
 
152                 NotAfter:  time.Now().Add(time.Hour * 24 * 3650),
```

如上，kubeadm生成的证书时间由一年变更为10年，其他版本编译过程差不多

1.9.4和1.13.3的kubeadm 二进制，10年签证的在我github上

<https://github.com/bbotte/bbotte.com/tree/master/kubeadm_binary>

源码在这里
<https://github.com/kubernetes/kubernetes/blob/release-1.9/staging/src/k8s.io/client-go/util/cert/cert.go#L107>



现在1.22的版本还需要更改一个文件中的时间

```
staging/src/k8s.io/client-go/util/cert/cert.go
```



如果修改错误，编译完成的话，先清理，再次编译即可

```
# ./build/make-clean.sh 
 
# make all WHAT=cmd/kubeadm GOFLAGS=-v
# ls _output/local/bin/linux/amd64/
conversion-gen  deepcopy-gen  defaulter-gen  go-bindata  kubeadm  openapi-gen  teststale
# _output/local/bin/linux/amd64/kubeadm version
kubeadm version: &version.Info{Major:"1", Minor:"9+", GitVersion:"v1.9.4-dirty", GitCommit:"bee2d1505c4fe820744d26d41ecd3fdd4a3d6546", GitTreeState:"dirty", BuildDate:"2019-01-29T08:45:42Z", GoVersion:"go1.11.5", Compiler:"gc", Platform:"linux/amd64"}
```

如果不编译新的kubeadm，就用原来的kubeadm，那么下面的操作会让证书时间延长一年

如果是新的集群，直接用此kubeadm创建集群好了，以下忽略。如果是正在运行的集群快要到期，用下面方式.
**以下步骤仅做参考,测试没通过，生产环境还是用修改构建后的kubeadm重新创建集群**

## 当前配置

以2台主机举例，1 master节点，1 node节点

```
[root@master ~]# cat /etc/hosts
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
192.168.12.40 master
192.168.12.18 node
```

### 当前状态

```
[root@master ~]# kubectl get no
NAME      STATUS    ROLES     AGE       VERSION
master    Ready     master    20d       v1.9.4
node      Ready     <none>    20d       v1.9.4
```

查询现在证书时间

```
# cd /etc/kubernetes/pki/
# for i in *.crt;do echo $i; openssl x509 -in $i -text -noout|egrep "Not Before|Not After";echo "-----------";done
            Not Before: Jan 29 06:34:48 2019 GMT
            Not After : Jan 29 06:34:49 2020 GMT
```

```
[root@master ~]# cat /etc/kubernetes/config.yaml 
apiVersion: kubeadm.k8s.io/v1alpha1
kind: MasterConfiguration
etcd:
  endpoints:
  - https://192.168.12.40:2379    #three master node
  - https://192.168.12.18:2379 
  caFile: /etc/etcd/ssl/ca.pem  #same as etcd ca
  certFile: /etc/etcd/ssl/etcd.pem 
  keyFile: /etc/etcd/ssl/etcd-key.pem
  dataDir: /var/lib/etcd
networking:
  podSubnet: 20.244.0.0/21
kubernetesVersion: 1.9.4
api:
  advertiseAddress: "192.168.12.40"   #kube-api VIP
token: "f6a0d5.ecf8a4377dc99bbe"
tokenTTL: "0s"
apiServerCertSANs:
- master
- 192.168.12.40
- 192.168.12.18
- 127.0.0.1
- kubernetes
- kubernetes.default
- kubernetes.default.svc
- kubernetes.default.svc.cluster
- kubernetes.default.svc.cluster.local
- 10.96.0.1
- 20.244.0.1
featureGates:
  CoreDNS: true
```

### 更换kubeadm

替换编译后的kubeadm

```
[root@master ~]# mv /usr/bin/kubeadm{,.bak}
[root@master ~]# cp _output/local/bin/linux/amd64/kubeadm /usr/bin/kubeadm
[root@master ~]# scp kubeadm node:/usr/bin/
```

## 更改配置

### kubelet配置和kube-controller-manager配置更改

kubelet配置（master和node都需要更改）

增加feature-gates

```
      --feature-gates=RotateKubeletClientCertificate=true,RotateKubeletServerCertificate=true
```

```
# vim /etc/systemd/system/kubelet.service.d/10-kubeadm.conf
[Service]
Environment="KUBELET_KUBECONFIG_ARGS=--bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf --kubeconfig=/etc/kubernetes/kubelet.conf --feature-gates=RotateKubeletClientCertificate=true,RotateKubeletServerCertificate=true"
```

kube-controller-manager配置（仅master）
增加feature-gates和experimental-cluster-signing-duration

```
     --feature-gates=RotateKubeletServerCertificate=true
     --experimental-cluster-signing-duration=87600h0m0s
```

```
# vim /etc/kubernetes/manifests/kube-controller-manager.yaml
    - --node-cidr-mask-size=24
    - --feature-gates=RotateKubeletServerCertificate=true
    - --experimental-cluster-signing-duration=87600h0m0s
    image: gcr.io/google_containers/kube-controller-manager-amd64:v1.9.4
```

### 添加ClusterRoleBinding绑定

```
# cat >> update.yaml <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: system:certificates.k8s.io:certificatesigningrequests:selfnodeserver
rules:
- apiGroups:
  - certificates.k8s.io
  resources:
  - certificatesigningrequests/selfnodeserver
  verbs:
  - create
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: kubeadm:node-autoapprove-certificate-server
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:certificates.k8s.io:certificatesigningrequests:selfnodeserver
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: Group
  name: system:nodes
EOF
[root@master ~]# kubectl apply -f update.yaml 
clusterrole "system:certificates.k8s.io:certificatesigningrequests:selfnodeserver" created clusterrolebinding "kubeadm:node-autoapprove-certificate-server" created
```

### 查看当前系统配置

```
[root@master ~]# ls /etc/kubernetes/
admin.conf               kubelet.conf             scheduler.conf
config.yaml              manifests/               ssl/
controller-manager.conf  pki/                     
[root@master ~]# ls /etc/kubernetes/pki/
apiserver.crt                 ca.crt              front-proxy-client.crt
apiserver.key                 ca.key              front-proxy-client.key
apiserver-kubelet-client.crt  front-proxy-ca.crt  sa.key
apiserver-kubelet-client.key  front-proxy-ca.key  sa.pub
```

## 更新证书

### 重新初始化kubernetes集群

备份，并使用更改时间的kubeadm重新初始化

```
[root@master ~]# cp -r /etc/kubernetes/ /tmp/
[root@master ~]# rm -f /etc/kubernetes/pki/apiserver* /etc/kubernetes/pki/front-proxy-client.*
[root@master ~]# kubeadm alpha phase certs apiserver --config /etc/kubernetes/config.yaml 
[certificates] Generated apiserver certificate and key.
[certificates] apiserver serving cert is signed for DNS names [master kubernetes kubernetes.default kubernetes.default.svc kubernetes.default.svc.cluster.local master kubernetes kubernetes.default kubernetes.default.svc kubernetes.default.svc.cluster kubernetes.default.svc.cluster.local] and IPs [10.96.0.1 192.168.12.40 192.168.12.40 192.168.12.18 127.0.0.1 10.96.0.1 20.244.0.1]
[root@master ~]# kubeadm alpha phase certs apiserver-kubelet-client --config /etc/kubernetes/config.yaml 
[certificates] Generated apiserver-kubelet-client certificate and key.
[root@master ~]# kubeadm alpha phase certs front-proxy-client --config /etc/kubernetes/config.yaml 
[certificates] Generated front-proxy-client certificate and key.
[root@master ~]# kubeadm alpha phase kubeconfig all --config /etc/kubernetes/config.yaml
[kubeconfig] Using existing up-to-date KubeConfig file: "admin.conf"
[kubeconfig] Using existing up-to-date KubeConfig file: "kubelet.conf"
[kubeconfig] Using existing up-to-date KubeConfig file: "controller-manager.conf"
[kubeconfig] Using existing up-to-date KubeConfig file: "scheduler.conf"
[root@master ~]# reboot
如果本机装有etcd的话，最好把etcd关闭后再重启
 
[root@master ~]# /bin/cp /etc/kubernetes/admin.conf .kube/config
```

#### master节点查看更新后证书

```
[root@master ~]# openssl x509 -in /etc/kubernetes/pki/apiserver-kubelet-client.crt -text -noout
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 296656465301295716 (0x41def7bc29b5264)
    Signature Algorithm: sha256WithRSAEncryption
        Issuer: CN=kubernetes
        Validity
            Not Before: Jan 29 06:34:48 2019 GMT
            Not After : Feb 16 02:48:51 2029 GMT
        Subject: O=system:masters, CN=kube-apiserver-kubelet-client
```

把生成的证书scp到其他master节点

### node节点操作

更改kubelet配置后重新加入集群

```
[root@node ~]# vim /etc/systemd/system/kubelet.service.d/10-kubeadm.conf
[root@node ~]# cp -r /etc/kubernetes/ /tmp/
[root@node ~]# rm -f /etc/kubernetes/pki/ca.crt /etc/kubernetes/kubelet.conf 
[root@node ~]# systemctl daemon-reload
[root@node ~]# systemctl stop kubelet
[root@node ~]# kubeadm join --token f6a0d5.ecf8a4377dc99bbe 192.168.12.40:6443 --discovery-token-ca-cert-hash sha256:51a0d767b6be6db863a7087fa1c872c45dcd7eeed3cf0eeeb88ca69df474fc45
[preflight] Running pre-flight checks.
	[WARNING FileExisting-crictl]: crictl not found in system path
[preflight] Starting the kubelet service
[discovery] Trying to connect to API Server "192.168.12.40:6443"
[discovery] Created cluster-info discovery client, requesting info from "https://192.168.12.40:6443"
[discovery] Requesting info from "https://192.168.12.40:6443" again to validate TLS against the pinned public key
[discovery] Cluster info signature and contents are valid and TLS certificate validates against pinned roots, will use API Server "192.168.12.40:6443"
[discovery] Successfully established connection with API Server "192.168.12.40:6443"
 
This node has joined the cluster:
* Certificate signing request was sent to master and a response
  was received.
* The Kubelet was informed of the new secure connection details.
 
Run 'kubectl get nodes' on the master to see this node join the cluster.
[root@node ~]# tail -f /var/log/messages
```

discovery-token 不记得？

```
[root@node ~]# kubeadm token generate
```

discovery-token-ca-cert-hash 忘了的话

```
[root@master ~]# openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | openssl dgst -sha256 -hex | sed 's/^.* //'
```

#### 在master查看node节点状态

```
[root@master ~]# kubectl get no
NAME      STATUS    ROLES     AGE       VERSION
master    Ready     master    20d       v1.9.4
node      Ready     <none>    20d       v1.9.4
[root@master ~]# kubectl get csr
NAME                                                   AGE       REQUESTOR                 CONDITION
csr-bd9q4                                              2m        system:node:master        Approved,Issued
csr-fvjpv                                              38s       system:node:node          Approved,Issued
node-csr-wiBwE2ZfO6brsCjPrgEqid4oSiUBGIeAyv0g3IZkur8   20d       system:bootstrap:f6a0d5   Approved,Issued
 
[root@node ~]# ll /var/lib/kubelet/pki/
total 20
-rw-r--r-- 1 root root  883 Feb 19 10:52 kubelet-client.crt
-rw------- 1 root root  227 Jan 29 14:44 kubelet-client.key
-rw-r--r-- 1 root root 1090 Jan 29 14:44 kubelet.crt
-rw------- 1 root root 1675 Jan 29 14:44 kubelet.key
-rw------- 1 root root 1220 Feb 19 10:52 kubelet-server-2019-02-19-10-52-26.pem
lrwxrwxrwx 1 root root   59 Feb 19 10:52 kubelet-server-current.pem -> /var/lib/kubelet/pki/kubelet-server-2019-02-19-10-52-26.pem
```

至此，证书更新完成

## 设计理论

### kubelet服务证书引导和自动更新过程说明

当kubelet首次启动时，它会生成一个自签名证书/密钥对，用于接受传入的TLS连接。 此过程涵盖了在本地生成密钥，然后向集群API服务器发出证书签名请求以获取由集群证书颁发机构签名的关联证书的过程等。此外，当证书接近过期时，将使用相同的机制来请求更新的证书。

#### kubelet启动步骤

1，查看本机现有的证书/密钥对，如果存在就使用
2，如果不存在，在kubelet当前生成密钥和证书的位置，生成一个密钥，创建证书签名请求，从API服务器请求签名证书，等待回应，将新证书/密钥对存储在–cert-dir指定的目录中

#### 证书到期的启动步骤

自动更新Kubelet服务器证书过程：通过生成新的私钥，向API服务器发出新的证书签名请求（CSR/Certificate Signing Request），安全地更新磁盘上的证书/密钥对，开始使用新的证书/密钥对

1，将新的证书/密钥对存储在–cert-dir指定的目录中，如果未指定，则将其存储在默认值中。 需允许kubelet有一个位置，用于存储在任何给定时刻可能具有的多个证书/密钥对（因为正在进行轮换）
2，将有一个特定功能来启用证书引导和轮转，RotateKubeletServerCertificate
3，将kubelet代码中的证书访问集中到CertificateManager。 CertificateManager将负责：
※ 提供用于建立TLS连接的正确证书。
※ 当前证书即将到期时生成新私钥并请求新证书。
※ 由于证书可以随时轮换，因此每次使用证书时，kubelet的所有其他部分都应向CertificateManager询问正确的证书。 除CertificateManager外没有证书缓存。
※ 在证书轮转正在进行中发生的kubelet崩溃或重新启动恢复（请求已发出但尚未签名等）
4，将更新节点的RBAC角色，以允许节点请求新证书。
5，让CertificateManager在证书过期时重复CSR过程。
※ 超过配置的持续时间阈值时，将请求新证书。
※ 确保正确安全的文件结构，包含下面5点
仅存在于内存中的私钥，如果中断就被放弃
当接收到相应的签名证书时，证书/密钥对将被写入单个文件，例如kubelet-server-.pem
将kubelet-server-updated.pem文件软连接到新的证书/秘钥对
删除kubelet-server-current.pem
将kubelet-server-updated.pem移动到kubelet-server-current.pem
6，证书请求签名（Certificate Request Signing）API被硬编码为颁发证书1年

## 实际过程

### 启用客户端证书轮换

kubelet 进程接收 –rotate-certificates 参数，该参数决定 kubelet 在当前使用的证书即将到期时， 是否会自动申请新的证书。 由于证书轮换是 beta 特性，必须通过参数 –feature-gates=RotateKubeletClientCertificate=true 进行启用。

kube-controller-manager 进程接收 –experimental-cluster-signing-duration 参数，该参数控制证书签发的有效期限。

### 理解证书轮换配置

当 kubelet 启动时，如被配置为自举（使用–bootstrap-kubeconfig 参数），kubelet 会使用其初始证书连接到 ，并发送证书签名的请求。 可以通过以下方式查看证书签名请求的状态：

```
kubectl get csr
```

最初，来自节点上 kubelet 的证书签名请求处于 Pending 状态。 如果证书签名请求满足特定条件， 控制管理器会自动批准，此时请求会处于 Approved 状态。 接下来，控制器管理器会签署证书， 证书的有效期限由 –experimental-cluster-signing-duration 参数指定，签署的证书会被附加到证书签名请求中。

Kubelet 会从 Kubernetes API 取回签署的证书，并将其写入磁盘，存储位置通过 –cert-dir 参数指定。 然后 kubelet 会使用新的证书连接到 Kubernetes API。

当签署的证书即将到期时，kubelet 会使用 Kubernetes API，发起新的证书签名请求。 同样地，控制管理器会自动批准证书请求，并将签署的证书附加到证书签名请求中。 Kubelet 会从 Kubernetes API 取回签署的证书，并将其写入磁盘。 然后它会更新与 Kubernetes API 的连接，使用新的证书重新连接到 Kubernetes API。

## 详细过程

### kubeadm与kubelet更新证书过程

当调用kubeadm init时，kubelet使用/var/lib/kubelet/config.yaml配置文件，并上传到群集中的ConfigMap(**kubectl describe configmap -n kube-system kubeadm-config** 命令查看)。ConfigMap名为kubelet-config-1.X，其中.X是您正在初始化的Kubernetes版本的次要版本。还将kubelet配置文件写入/etc/kubernetes/kubelet.conf，并为群集中的所有kubelet提供基线群集(baseline cluster-wide)范围配置。此配置文件指向允许kubelet与API服务器通信的客户端证书。这解决了将群集级配置传播到每个kubelet的需要。

初始化集群的时候已经指定了token( **kubeadm token generate **命令生成) ，node节点 join master节点也写明了此token。kubelet要向 kube-apiserver 请求客户端证书，kubelet要使用含有bootstrap token的 kubeconfig文件向kube-apiserver发送请求，此kubeconfig在credentials中指定要调用的token文件名称必须是kubelet-bootstrap。如果 –kubeconfig 指定的文件不存在，则使用 bootstrap kubeconfig 向 API server 请求客户端证书。证书请求审批通过后， kubelet 把生成的密钥和证书的信息写入由 -kubeconfig 指定路径的文件中。证书和密钥文件将被放置在由 –cert-dir 指定的目录中。

API服务器中的Bootstrap Authenticator会读取由token信息组成的Secrets。node节点执行 kubeadm join 时，kubeadm使用Bootstrap Token凭据执行TLS引导程序，该引导程序获取下载kubelet-config-1.X ConfigMap所需的凭据并将其写入/var/lib/kubelet/config.yaml。动态环境文件的生成方式与kubeadm init完全相同。在kubelet加载新配置之后，kubeadm会写入/etc/kubernetes/bootstrap-kubelet.conf KubeConfig文件，该文件包含CA证书和Bootstrap Token。这些由kubelet用于执行TLS Bootstrap并获得唯一的凭证，该凭证存储在/etc/kubernetes/kubelet.conf中。写入此文件后，kubelet已完成执行TLS Bootstrap

kubelet 使用的 bootstrap.kubeconfig 配置文件中包含apiserver的ca证书和此token，与 apiserver 建立 TLS 通讯，使用 bootstrap.kubeconfig 中的用户 Token等信息组成的secret 来向 apiserver 声明自己的 RBAC 授权身份

在默认情况下，kubelet 通过 bootstrap.kubeconfig 中的预设用户 Token 声明了自己的身份，然后创建 CSR 请求，1.9版本中默认是允许的。用于TLS Bootstrap的KubeConfig文件是/etc/kubernetes/bootstrap-kubelet.conf，但仅在/etc/kubernetes/kubelet.conf不存在时使用。

kube-controller-manager 默认签发证书时间是1年，所以要更改时间，对 kubelet 发起的特定 CSR 请求自动批准即可，TLS bootstrapping 时的证书实际是由 kube-controller-manager 组件来签署的。CSR请求自动批准需要我们授予RBAC权限来完成。有两组不同的权限：
※ nodeclient：如果节点正在为节点创建新证书，则它还没有证书。它使用上面列出的一个令牌进行身份验证，因此是该群组的一部分system:bootstrappers。
※ selfnodeclient：如果某个节点正在续订其证书，那么它已经拥有一个证书（根据定义），它会连续使用该证书作为该组的一部分进行身份验证system:nodes。

要使kubelet能够请求和接收新证书，请创建一个ClusterRoleBinding将引导节点所属的组绑定system:bootstrappers到ClusterRole授予其权限的组，即system:certificates.k8s.io:certificatesigningrequests:nodeclient。即上面配置的update.yaml

### 证书自动续期

1. kubelet 读取 bootstrap.kubeconfig，使用其 CA 与 Token 向 apiserver 发起第一次 CSR 请求(nodeclient)
2. apiserver 根据 RBAC 规则自动批准首次 CSR 请求(approve-node-client-csr)，并下发证书(kubelet-client.crt)
3. kubelet 使用刚刚签发的证书(O=system:nodes, CN=system:node:NODE_NAME)与 apiserver 通讯，并发起申请kubelet(10250端口) 所使用证书的 CSR 请求
4. apiserver 根据 RBAC 规则自动批准 kubelet 为其 10250 端口申请的证书(kubelet-server-current.crt)
5. 证书即将到期时，kubelet 自动向 apiserver 发起用于与 apiserver 通讯所用证书的 renew CSR 请求和 renew 本身 kubelet(10250端口) 端口所用证书的 CSR 请求
6. apiserver 根据 RBAC 规则自动批准两个证书
7. kubelet 拿到新证书后关闭所有连接，reload 新证书，以后便一直如此

### 参考

<https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet-tls-bootstrapping/>

<https://k8smeetup.github.io/docs/tasks/tls/certificate-rotation/>

<https://kubernetes.io/docs/reference/setup-tools/kubeadm/kubeadm-init-phase/>

<https://sealyun.com/post/kubeadm-dev/>

<https://github.com/kubernetes/kubeadm/issues/581>

<https://k8smeetup.github.io/docs/tasks/administer-cluster/kubeadm-upgrade-ha/>

<https://k8smeetup.github.io/docs/admin/kubelet-tls-bootstrapping/>

<https://kubernetes.io/zh/docs/reference/setup-tools/kubeadm/kubeadm-init/>

1.13的版本准备拿来用，把1.9改为1.13版本
支持外部自签名的证书（避免更换一次证书）
支持自定义镜像仓库（避免从谷歌拉取不到镜像）

2019年02月20日 于 [linux工匠](https://bbotte.github.io/) 发表