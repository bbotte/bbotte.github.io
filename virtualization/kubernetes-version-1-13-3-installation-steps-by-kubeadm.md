---
layout: default
---

# kubeadm安装1.13.3版本kubernetes步骤

1. kubernetes 1.13版本功能更新
2. etcd: read-only range request took too long bug
3. 系统初始化
4. 安装docker18.09
5. 安装kubelet、kubeadm、kubectl
6. 配置kubeconfig
7. kubeadm初始化集群
8. 安装网络插件kube-router
9. 查看pod状态
10. node节点加入集群
11. 安装dashboard、traefik、metric
12. 其他信息

kubeadm安装1.13.3版本kubernetes步骤

文档也可以看github <https://bbotte.github.io/virtualization/kubernetes_cluster_install_1-13-3>

### kubernetes 1.13版本功能更新

kubeadm自动化创建集群功能 stable
支持自定义node和pod(10.96.0.0/12)运行的网段
默认的cluster.local domain可以更改为自定义域名
支持外部证书，如果提供了证书，kubeadm init就不会再创建证书
k8s.gcr.io默认的镜像(kubeadm config images list)可以改为自定义镜像
DNS以CoreDNS为默认 stable
kubelet发现本地插件(比如容器存储接口CSI, GPU)功能 stable
对Windows容器支持 beta
新增kubecrl diff命令(kubectl diff -f something.yaml -f somethingelse.yaml LOCAL MERGED)
对第三方监控的支持 alpha

```
# kubeadm -h
    ┌──────────────────────────────────────────────────────────┐
    │ On the first machine:                                    │
    ├──────────────────────────────────────────────────────────┤
    │ control-plane# kubeadm init                              │
    └──────────────────────────────────────────────────────────┘
 
    ┌──────────────────────────────────────────────────────────┐
    │ On the second machine:                                   │
    ├──────────────────────────────────────────────────────────┤
    │ worker# kubeadm join <arguments-returned-from-init>      │
    └──────────────────────────────────────────────────────────┘
```

### tcd: read-only range request took too long bug

务必安装etcd 3.3.13以上版本，避免 etcd read-only range request took too long

etcd 版本为3.3.11，有bug，不要使用

![kubeadm安装1.13.3版本kubernetes步骤 - 第1张](../images/2019/02/%E5%BE%AE%E4%BF%A1%E6%88%AA%E5%9B%BE_20190710105346.png)

https://github.com/kubernetes/kubernetes/issues/70082

https://github.com/etcd-io/etcd/issues/10860

因为etcd长时间没有响应，所以controller-manager  、 scheduler多次重启

![kubeadm安装1.13.3版本kubernetes步骤 - 第2张](../images/2019/02/%E5%BE%AE%E4%BF%A1%E5%9B%BE%E7%89%87_20190710105636.png)

etcd-v3.3.13版本此bug已修复，测试环境和生产建议用大于等于3.3.13版本的etcd

### 系统初始化

参考[kubernetes1.9版本集群配置向导](http://bbotte.com/kvm-xen/kubernetes-1-9-version-cluster-configuration-wizard/)

```
yum install ipvsadm ipset -y
 
cat > /etc/sysconfig/modules/ipvs.modules <<EOF
#!/bin/bash
modprobe -- ip_vs
modprobe -- ip_vs_rr
modprobe -- ip_vs_wrr
modprobe -- ip_vs_sh
modprobe -- nf_conntrack_ipv4
EOF
chmod 755 /etc/sysconfig/modules/ipvs.modules && bash /etc/sysconfig/modules/ipvs.modules && lsmod | grep -e ip_vs -e nf_conntrack_ipv4
```

### 安装docker18.09

```
yum remove docker-ce -y
rm -rf /var/lib/docker
yum remove kubeadm kubectl kubelet kubernetes-cni -y
rm -rf /var/lib/kubelet/
阿里云 https://mirrors.aliyun.com/docker-ce/linux/centos/7/x86_64/stable/Packages/ 下载rpm包
yum localinstall docker-ce-18.09.2-3.el7.x86_64.rpm containerd.io-1.2.2-3.el7.x86_64.rpm docker-ce-cli-18.09.2-3.el7.x86_64.rpm container-selinux-2.74-1.el7.noarch.rpm
cat <<EOF>> /etc/docker/daemon.json 
{
  "exec-opts": ["native.cgroupdriver=cgroupfs"],
  "insecure-registries":["harbor.bbotte.com"]
}
EOF
systemctl enable docker
systemctl start docker
```

### 安装kubelet、kubeadm、kubectl

1.阿里云源安装kubelet、kubeadm、kubectl

```
cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
exclude=kube*
EOF
yum install -y kubelet kubeadm kubectl --disableexcludes=kubernetes
systemctl enable --now kubelet
```

2.本地安装kubelet、kubeadm、kubectl

```
cd k8s/rpm/
yum localinstall cri-tools-1.12.0-0.x86_64.rpm  kubelet-1.13.3-0.x86_64.rpm  kubeadm-1.13.3-0.x86_64.rpm kubernetes-cni-0.6.0-0.x86_64.rpm kubectl-1.13.3-0.x86_64.rpm
```

### 配置kubeconfig

查看默认配置

```
kubeadm config print-defaults > defaults_config.yaml
 
kubeadm config print init-defaults > config.yaml
```

下面是修改过的配置，更改了service和pod的ip网段,因为网段和公司网络有冲突，一般不需要更改网段

```
[root@master ~]# cat k8s/config.yaml 
apiVersion: kubeadm.k8s.io/v1beta1
bootstrapTokens:
- groups:
  - system:bootstrappers:kubeadm:default-node-token
  token: exunrz.av851fhplszl6nem # kubeadm token generate
  ttl: 108h0m0s
  usages:
  - signing
  - authentication
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: 192.168.12.40 #api VIP
  bindPort: 6443
nodeRegistration:
  criSocket: /var/run/dockershim.sock
  name: master                       #这里是主机名称，如果是3个master，这里名称需要更改
  taints:
  - effect: NoSchedule
    key: node-role.kubernetes.io/master
---
apiServer:
  timeoutForControlPlane: 4m0s
  CertSANs:
  - master                    # etcd name
  - node
  - 192.168.12.40             # master IP
  - 127.0.0.1
  - kubernetes
  - kubernetes.default
  - kubernetes.default.svc
  - kubernetes.default.svc.cluster
  - kubernetes.default.svc.cluster.local
  - 10.100.0.1                 # podSubnet
  - 10.200.0.1                 # serviceSubnet
apiVersion: kubeadm.k8s.io/v1beta1
certificatesDir: /etc/kubernetes/pki
clusterName: kubernetes
controlPlaneEndpoint: "192.168.12.40:6443"  #api VIP
controllerManager: {}
dns:
  type: CoreDNS
etcd:
  external:
    endpoints:
    - https://192.168.12.40:2379    #three etcd node
    - https://192.168.12.18:2379 
    caFile: /etc/etcd/ssl/ca.pem    #same as /etc/etcd/etcd.conf ca
    certFile: /etc/etcd/ssl/etcd.pem 
    keyFile: /etc/etcd/ssl/etcd-key.pem
imageRepository: registry.cn-hangzhou.aliyuncs.com/google_containers #your define docker registry
kind: ClusterConfiguration
kubernetesVersion: v1.13.3
networking:
  dnsDomain: cluster.local
  podSubnet: "10.100.0.0/17"   #pod ip address segment,every server has a ip segment, this network segment supports up to 127 hosts.
  serviceSubnet: 10.200.0.0/19 #service ip address segment,this network segment supports up to 8190 services.
scheduler: {}
---
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: "ipvs"
---
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
clusterDNS:
- 10.200.0.10
```

默认配置可以用print打印：   kubeadm config print init-defaults > def.yaml 



### kubeadm初始化集群

用已生成的证书或者直接以上面配置文件初始化都可以
把已生成、过期时间为10年的证书放到 /etc/kubernetes/pki 文件夹，或者复制kubeadm二进制文件，再初始化集群

```
# cp k8s/rpm/kubeadm /usr/bin/kubeadm
```

此kubeadm即更改 vendor/k8s.io/client-go/util/cert/cert.go 证书过期时间为10年时间的kubeadm

```
# diff cert.go vendor/k8s.io/client-go/util/cert/cert.go 
112c112
< 		NotAfter:     time.Now().Add(duration365d).UTC(),
---
> 		NotAfter:     time.Now().Add(duration365d * 10).UTC(),
159c159
< 	maxAge := time.Hour * 24 * 365          // one year self-signed certs
---
> 	maxAge := time.Hour * 24 * 365 * 10         // one year self-signed certs
```

```
kubeadm init --config k8s/config.yaml
[init] Using Kubernetes version: v1.13.3
[preflight] Running pre-flight checks
	[WARNING SystemVerification]: this Docker version is not on the list of validated versions: 18.09.2. Latest validated version: 18.06
[preflight] Pulling images required for setting up a Kubernetes cluster
[preflight] This might take a minute or two, depending on the speed of your internet connection
[preflight] You can also perform this action in beforehand using 'kubeadm config images pull'
[kubelet-start] Writing kubelet environment file with flags to file "/var/lib/kubelet/kubeadm-flags.env"
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
[kubelet-start] Activating the kubelet service
[certs] Using certificateDir folder "/etc/kubernetes/pki"
[certs] Using existing ca certificate authority
[certs] Using existing apiserver certificate and key on disk
[certs] Using existing apiserver-kubelet-client certificate and key on disk
[certs] Using existing front-proxy-ca certificate authority
[certs] Using existing front-proxy-client certificate and key on disk
[certs] External etcd mode: Skipping etcd/ca certificate authority generation
[certs] External etcd mode: Skipping etcd/peer certificate authority generation
[certs] External etcd mode: Skipping etcd/healthcheck-client certificate authority generation
[certs] External etcd mode: Skipping apiserver-etcd-client certificate authority generation
[certs] External etcd mode: Skipping etcd/server certificate authority generation
[certs] Using the existing "sa" key
[kubeconfig] Using kubeconfig folder "/etc/kubernetes"
[kubeconfig] Writing "admin.conf" kubeconfig file
[kubeconfig] Writing "kubelet.conf" kubeconfig file
[kubeconfig] Writing "controller-manager.conf" kubeconfig file
[kubeconfig] Writing "scheduler.conf" kubeconfig file
[control-plane] Using manifest folder "/etc/kubernetes/manifests"
[control-plane] Creating static Pod manifest for "kube-apiserver"
[control-plane] Creating static Pod manifest for "kube-controller-manager"
[control-plane] Creating static Pod manifest for "kube-scheduler"
[wait-control-plane] Waiting for the kubelet to boot up the control plane as static Pods from directory "/etc/kubernetes/manifests". This can take up to 4m0s
[apiclient] All control plane components are healthy after 22.508238 seconds
[uploadconfig] storing the configuration used in ConfigMap "kubeadm-config" in the "kube-system" Namespace
[kubelet] Creating a ConfigMap "kubelet-config-1.13" in namespace kube-system with the configuration for the kubelets in the cluster
[patchnode] Uploading the CRI Socket information "/var/run/dockershim.sock" to the Node API object "master" as an annotation
[mark-control-plane] Marking the node master as control-plane by adding the label "node-role.kubernetes.io/master=''"
[mark-control-plane] Marking the node master as control-plane by adding the taints [node-role.kubernetes.io/master:NoSchedule]
[bootstrap-token] Using token: 4a9c67.b2a0c0675c51ba5a
[bootstrap-token] Configuring bootstrap tokens, cluster-info ConfigMap, RBAC Roles
[bootstraptoken] configured RBAC rules to allow Node Bootstrap tokens to post CSRs in order for nodes to get long term certificate credentials
[bootstraptoken] configured RBAC rules to allow the csrapprover controller automatically approve CSRs from a Node Bootstrap Token
[bootstraptoken] configured RBAC rules to allow certificate rotation for all node client certificates in the cluster
[bootstraptoken] creating the "cluster-info" ConfigMap in the "kube-public" namespace
[addons] Applied essential addon: CoreDNS
[addons] Applied essential addon: kube-proxy
 
Your Kubernetes master has initialized successfully!
 
To start using your cluster, you need to run the following as a regular user:
 
  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config
 
You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
  https://kubernetes.io/docs/concepts/cluster-administration/addons/
 
You can now join any number of machines by running the following on each node
as root:
 
  kubeadm join 192.168.12.40:6443 --token 4a9c67.b2a0c0675c51ba5a --discovery-token-ca-cert-hash sha256:f58ecXXX
```

贴上面一段主要是看明白kubeadm初始化的过程

kubernetes 1.13版本支持自定义证书，即自己创建有关kubernetes的证书，放到默认目录 /etc/kubernetes/pki ，kubeadm init的时候就会使用里面的证书，而不会重新创建

```
/bin/cp /etc/kubernetes/admin.conf $HOME/.kube/config
kubectl get cs
```



#### 另：kubernetes 1.20的coredns问题：network: open /run/flannel/subnet.env: no such file or directory,如果用的网络插件是flannel

```
  Warning  FailedCreatePodSandBox  1s (x4 over 8s)    kubelet            (combined from similar events): Failed to create pod sandbox: rpc error: code = Unknown desc = failed to set up sandbox container 'xxxx' network for pod "coredns-54d67798b7-db6c8": networkPlugin cni failed to set up pod "coredns-54d67798b7-db6c8_kube-system" network: open /run/flannel/subnet.env: no such file or directory
```

如果是上述网络配置，那么添加flannel的subnet.env文件后，coredns服务才能启动

```
# cat /run/flannel/subnet.env 
FLANNEL_NETWORK=10.100.0.0/17
FLANNEL_SUBNET=10.100.0.1/19
FLANNEL_MTU=1450
FLANNEL_IPMASQ=true
```



### 安装网络插件kube-router

```
wget https://raw.githubusercontent.com/cloudnativelabs/kube-router/master/daemonset/kubeadm-kuberouter-all-features.yaml
kubectl apply -f k8s/network/kubeadm-kuberouter-all-features.yaml
```

此kube-router版本为 v0.2.5

```
sleep 20
docker run --privileged -v /lib/modules:/lib/modules --net=host registry.cn-hangzhou.aliyuncs.com/google_containers/kube-proxy:v1.13.3 kube-proxy --cleanup
kubectl -n kube-system delete ds kube-proxy
```

### 查看pod状态

```
[root@master ~]# kubectl get po -n kube-system
NAME                             READY   STATUS    RESTARTS   AGE
coredns-89cc84847-dgjs2          1/1     Running   0          2m14s
coredns-89cc84847-j22nq          1/1     Running   0          2m14s
kube-apiserver-master            1/1     Running   0          75s
kube-controller-manager-master   1/1     Running   0          95s
kube-router-xjwgw                1/1     Running   0          50s
kube-scheduler-master            1/1     Running   0          84s
[root@master ~]# kubectl get po -n kube-system -o wide
NAME                             READY   STATUS    RESTARTS   AGE     IP              NODE     NOMINATED NODE   READINESS GATES
coredns-89cc84847-dgjs2          1/1     Running   0          2m28s   10.100.0.2      master   <none>           <none>
coredns-89cc84847-j22nq          1/1     Running   0          2m28s   10.100.0.3      master   <none>           <none>
kube-apiserver-master            1/1     Running   0          89s     192.168.12.40   master   <none>           <none>
kube-controller-manager-master   1/1     Running   0          109s    192.168.12.40   master   <none>           <none>
kube-router-xjwgw                1/1     Running   0          64s     192.168.12.40   master   <none>           <none>
kube-scheduler-master            1/1     Running   0          98s     192.168.12.40   master   <none>           <none>
```

```
[root@master ~]# kubectl cluster-info
Kubernetes master is running at https://192.168.12.40:6443
KubeDNS is running at https://192.168.12.40:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

如果是3台master做高可用，那么复制证书文件夹 /etc/kubernetes/pki/ 和config.yaml配置到其他master节点，同样kubeadm init 初始化即可，当然，api server的IP 是 3台master的 VIP

### node节点加入集群

```
[root@node ~]# kubeadm join 192.168.12.40:6443 --token 4a9c67.b2a0c0675c51ba5a --discovery-token-ca-cert-hash sha256:f58a5ad8XXX
[preflight] Running pre-flight checks
	[WARNING SystemVerification]: this Docker version is not on the list of validated versions: 18.09.2. Latest validated version: 18.06
[discovery] Trying to connect to API Server "192.168.12.40:6443"
[discovery] Created cluster-info discovery client, requesting info from "https://192.168.12.40:6443"
[discovery] Requesting info from "https://192.168.12.40:6443" again to validate TLS against the pinned public key
[discovery] Cluster info signature and contents are valid and TLS certificate validates against pinned roots, will use API Server "192.168.12.40:6443"
[discovery] Successfully established connection with API Server "192.168.12.40:6443"
[join] Reading configuration from the cluster...
[join] FYI: You can look at this config file with 'kubectl -n kube-system get cm kubeadm-config -oyaml'
[kubelet] Downloading configuration for the kubelet from the "kubelet-config-1.13" ConfigMap in the kube-system namespace
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
[kubelet-start] Writing kubelet environment file with flags to file "/var/lib/kubelet/kubeadm-flags.env"
[kubelet-start] Activating the kubelet service
[tlsbootstrap] Waiting for the kubelet to perform the TLS Bootstrap...
[patchnode] Uploading the CRI Socket information "/var/run/dockershim.sock" to the Node API object "node" as an annotation
 
This node has joined the cluster:
* Certificate signing request was sent to apiserver and a response was received.
* The Kubelet was informed of the new secure connection details.
 
Run 'kubectl get nodes' on the master to see this node join the cluster.
```

### 安装dashboard、traefik、metric

```
[root@master ~]# kubectl apply -f k8s/dashboard/
secret/kubernetes-dashboard-certs created
serviceaccount/kubernetes-dashboard created
role.rbac.authorization.k8s.io/kubernetes-dashboard-minimal created
rolebinding.rbac.authorization.k8s.io/kubernetes-dashboard-minimal created
deployment.apps/kubernetes-dashboard created
service/kubernetes-dashboard created
[root@master ~]# kubectl apply -f k8s/traefik/
serviceaccount/traefik-ingress-controller created
daemonset.extensions/traefik-ingress-controller created
service/traefik-ingress-service created
clusterrole.rbac.authorization.k8s.io/traefik-ingress-controller created
clusterrolebinding.rbac.authorization.k8s.io/traefik-ingress-controller created
service/traefik-web-ui created
ingress.extensions/traefik-web-ui created
[root@master ~]# kubectl apply -f k8s/monitor/
clusterrole.rbac.authorization.k8s.io/system:aggregated-metrics-reader created
clusterrolebinding.rbac.authorization.k8s.io/metrics-server:system:auth-delegator created
rolebinding.rbac.authorization.k8s.io/metrics-server-auth-reader created
apiservice.apiregistration.k8s.io/v1beta1.metrics.k8s.io created
serviceaccount/metrics-server created
deployment.extensions/metrics-server created
service/metrics-server created
clusterrole.rbac.authorization.k8s.io/system:metrics-server created
clusterrolebinding.rbac.authorization.k8s.io/system:metrics-server created
```

### 其他信息

查看证书时间

```
[root@master ~]# openssl x509 -in /etc/kubernetes/pki/apiserver-kubelet-client.crt -text -noout
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 8252480188942790293 (0x7286b30221e22e95)
    Signature Algorithm: sha256WithRSAEncryption
        Issuer: CN=kubernetes
        Validity
            Not Before: Feb 28 02:35:07 2019 GMT
            Not After : Feb 25 02:35:08 2029 GMT
        Subject: O=system:masters, CN=kube-apiserver-kubelet-client
```

dashboard访问链接: https://api_VIP:6443/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/login

有关**traefik**需要说明一下，我提了一个push <https://github.com/containous/traefik/pull/4534>

参考: <https://kubernetes.io/zh/docs/reference/setup-tools/kubeadm/kubeadm-init/>

度娘网盘离线配置及rpm/images包: https://pan.baidu.com/s/1GUMEAvezRxTw1q7uadAZaQ  提取码：ot16

如果k8s集群是二进制安装，不是上面的kubeadm，coredns配置需要更改下:

```
wget https://raw.githubusercontent.com/coredns/deployment/master/kubernetes/deploy.sh
wget https://raw.githubusercontent.com/coredns/deployment/master/kubernetes/coredns.yaml.sed
REVERSE_CIDR=$(grep service-cluster-ip-range /etc/kubernetes/manifests/kube-apiserver.yaml|awk -F'=' '{print $2}')
CLUSTER_DNS_IP=$(kubectl get service -n kube-system kube-dns -o jsonpath="{.spec.clusterIP}")
CLUSTER_DOMAIN=$(grep clusterDomain /var/lib/kubelet/config.yaml |awk '{print $2}')
/bin/bash deploy.sh -s -r $REVERSE_CIDR -i $CLUSTER_DNS_IP -d $CLUSTER_DOMAIN -t coredns.yaml.sed > coredns.yaml
kubectl apply -f coredns.yaml
```

其他配置和kubernetes 1.9的版本没太大区别

2019年02月28日 于 [linux工匠](https://bbotte.github.io/) 发表

