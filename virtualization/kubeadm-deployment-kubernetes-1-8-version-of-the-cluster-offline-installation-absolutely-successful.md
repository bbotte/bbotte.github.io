---
layout: default
---

# kubeadm部署kubernetes 1.8离线安装绝对成功版

1. 版本说明
2. 系统初始化设置
3. 安装docker
4. 启动docker服务
5. 导入kubernetes镜像并安装kubernetes rpm包
6. kubeadm初始化
7. calico组件安装
8. node节点配置
9. dashboard组件安装
10. 常用命令
11. 重置集群
12. 查看服务状态
13. k8s 1.8集群配置

### **版本说明**

文章不注明所用的版本就是扯淡淡：
系统: centos 7.4
docker: 17.03.0-ce
cgroupdriver: systemd
kubernetes: 1.8.2

```
kubelet: v1.8.2
kubectl: v1.8.2
kubeadm: v1.8.2
```

docker images包

```
REPOSITORY                                               TAG 
quay.io/calico/node                                      v2.6.3 
index.tenxcloud.com/jimmy/kubernetes-dashboard-amd64     v1.8.0 
quay.io/calico/kube-controllers                          v1.0.1 
quay.io/calico/cni                                       v1.11.1 
gcr.io/google_containers/kube-apiserver-amd64            v1.8.2 
gcr.io/google_containers/kube-controller-manager-amd64   v1.8.2 
gcr.io/google_containers/kube-scheduler-amd64            v1.8.2 
gcr.io/google_containers/kube-proxy-amd64                v1.8.2 
gcr.io/google_containers/kubernetes-dashboard-init-amd64 v1.0.1 
gcr.io/google_containers/k8s-dns-sidecar-amd64           1.14.5 
gcr.io/google_containers/k8s-dns-kube-dns-amd64          1.14.5 
gcr.io/google_containers/k8s-dns-dnsmasq-nanny-amd64     1.14.5 
quay.io/coreos/etcd                                      v3.1.10 
gcr.io/google_containers/etcd-amd64                      3.0.17 
gcr.io/google_containers/pause-amd64                     3.0
```

下面用2台主机实验，1 master节点，1 node节点，IP_Address:

```
master_ip 192.168.22.78
node_ip 192.168.22.79
```

kubernetes离线安装百度盘链接：链接：https://pan.baidu.com/s/1nvOh7WP 密码：3csk

### **系统初始化设置**

```
# cat /etc/centos-release
CentOS Linux release 7.4.1708 (Core)
 
hostnamectl --static set-hostname master/node
exec $SHELL
cat <<EOF >> /etc/hosts
192.168.22.78 master
192.168.22.79 node
EOF
yum install vim epel-release ntpdate tree lrzsz sysstat dstat wget mlocate mtr lsof bind-utils -y
ntpdate ntp1.aliyun.com
swapoff -a
systemctl stop firewalld
systemctl disable firewalld
sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config 
setenforce 0
iptables -P FORWARD ACCEPT
cat <<EOF >  /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
vm.swappiness=0
EOF
sysctl --system
```

### **安装docker**

1. 下载docker到本地 <https://download.docker.com/linux/centos/7/x86_64/stable/Packages/>

解压压缩包，进入k8s_1.8.2/k8s_1.8.2_docker/目录，安装即可

```
docker-ce-17.03.0.ce-1.el7.centos.x86_64.rpm
docker-ce-selinux-17.03.0.ce-1.el7.centos.noarch.rpm
yum localinstall *.rpm -y
```

2. 或者yum指定版本安装

```
wget https://download.docker.com/linux/centos/docker-ce.repo -O /etc/yum.repos.d/docker-ce.repo
yum list docker-ce.x86_64 --showduplicates
yum install docker-ce.x86_64 -y
```

3. 注：此系统不建议直接yum直接安装docker

```
# yum install -y docker #不要yum直接安装此docker
如果docker此版本docker cgroup-driver默认是systemd，如果改为cgroupfs就不能启动，而kubelet cgroup-driver默认是cgroupfs，
改为systemd，配合systemd的docker的话，需要设置kubeadm-aio 见：https://docs.openstack.org/openstack-helm/latest/install/developer/all-in-one.html
```

### **启动docker服务**

```
systemctl enable docker && systemctl start docker && systemctl status docker && docker info
# docker info
Containers: 0
Running: 0
Paused: 0
Stopped: 0
Images: 0
Server Version: 17.03.0-ce
Storage Driver: overlay
Backing Filesystem: xfs
Supports d_type: true
Logging Driver: json-file
Cgroup Driver: cgroupfs
```

默认的Cgroup Driver是systemd，docker需要和kubelet统一cgroup

Cgroup Driver默认是systemd，修改docker的cgroup driver

```
# cat << EOF > /etc/docker/daemon.json
{
"exec-opts": ["native.cgroupdriver=systemd"]
}
EOF
systemctl restart docker
docker info|grep Cgroup
```

### **导入kubernetes镜像并安装kubernetes rpm包**

本地导出所有镜像，这一步不用做：

```
for i in `docker images|grep -v TAG|awk 'NF>1{print $1":"$2}'`;do docker save -o `echo $i|sed 's#/#-#g'`.tar $i;done
```

解压压缩包，进入k8s_1.8.2/k8s_1.8.2_images/目录，**导入kubernetes镜像**

```
# ls
gcr.io-google_containers-etcd-amd64:3.0.17.tar
gcr.io-google_containers-k8s-dns-dnsmasq-nanny-amd64:1.14.5.tar
gcr.io-google_containers-k8s-dns-kube-dns-amd64:1.14.5.tar
gcr.io-google_containers-k8s-dns-sidecar-amd64:1.14.5.tar
gcr.io-google_containers-kube-apiserver-amd64:v1.8.2.tar
gcr.io-google_containers-kube-controller-manager-amd64:v1.8.2.tar
gcr.io-google_containers-kube-proxy-amd64:v1.8.2.tar
gcr.io-google_containers-kubernetes-dashboard-init-amd64:v1.0.1.tar
gcr.io-google_containers-kube-scheduler-amd64:v1.8.2.tar
gcr.io-google_containers-pause-amd64:3.0.tar
index.tenxcloud.com-jimmy-kubernetes-dashboard-amd64:v1.8.0.tar
quay.io-calico-cni:v1.11.1.tar
quay.io-calico-kube-controllers:v1.0.1.tar
quay.io-calico-node:v2.6.3.tar
quay.io-coreos-etcd:v3.1.10.tar
 
for i in `ls .`;do docker load < $i;done
```

解压压缩包，进入k8s_1.8.2/k8s_1.8.2_rpm/目录，**安装kubernetes rpm包**

```
# ls
kubeadm-1.8.2-0.x86_64.rpm  kubernetes-cni-0.5.1-1.x86_64.rpm
kubectl-1.8.2-0.x86_64.rpm  socat-1.7.3.2-2.el7.x86_64.rpm
kubelet-1.8.2-0.x86_64.rpm
 
yum localinstall *.rpm -y
```

```
# systemctl enable kubelet && systemctl start kubelet
```

这时候kubelet服务是没有启动的，kubeadm init后才会bind 10255端口

```
# systemctl status kubelet -l
● kubelet.service - kubelet: The Kubernetes Node Agent
Loaded: loaded (/etc/systemd/system/kubelet.service; enabled; vendor preset: disabled)
Drop-In: /etc/systemd/system/kubelet.service.d
└─10-kubeadm.conf
Active: activating (auto-restart) (Result: exit-code)
```

如果修改了kubelet的配置文件，比如/etc/systemd/system/kubelet.service.d/10-kubeadm.conf 需要重新加载服务

```
# journalctl -xeu kubelet
# systemctl daemon-reload
```

kubeadm init初始化后kubelet服务才会active

```
# kubelet
listen tcp 0.0.0.0:10255: bind: address already in use
# lsof -i:10255
```

### **kubeadm初始化**

```
# kubeadm init --pod-network-cidr=10.244.0.0/16 --kubernetes-version v1.8.2 --skip-preflight-checks
[kubeadm] WARNING: kubeadm is in beta, please do not use it for production clusters.
[init] Using Kubernetes version: v1.8.2
[init] Using Authorization modes: [Node RBAC]
[preflight] Skipping pre-flight checks
[kubeadm] WARNING: starting in 1.8, tokens expire after 24 hours by default (if you require a non-expiring token use --token-ttl 0)
[certificates] Generated ca certificate and key.
[certificates] Generated apiserver certificate and key.
[certificates] apiserver serving cert is signed for DNS names [master kubernetes kubernetes.default kubernetes.default.svc kubernetes.default.svc.cluster.local] and IPs [10.96.0.1 192.168.22.78]
[certificates] Generated apiserver-kubelet-client certificate and key.
[certificates] Generated sa key and public key.
[certificates] Generated front-proxy-ca certificate and key.
[certificates] Generated front-proxy-client certificate and key.
[certificates] Valid certificates and keys now exist in "/etc/kubernetes/pki"
[kubeconfig] Wrote KubeConfig file to disk: "admin.conf"
[kubeconfig] Wrote KubeConfig file to disk: "kubelet.conf"
[kubeconfig] Wrote KubeConfig file to disk: "controller-manager.conf"
[kubeconfig] Wrote KubeConfig file to disk: "scheduler.conf"
[controlplane] Wrote Static Pod manifest for component kube-apiserver to "/etc/kubernetes/manifests/kube-apiserver.yaml"
[controlplane] Wrote Static Pod manifest for component kube-controller-manager to "/etc/kubernetes/manifests/kube-controller-manager.yaml"
[controlplane] Wrote Static Pod manifest for component kube-scheduler to "/etc/kubernetes/manifests/kube-scheduler.yaml"
[etcd] Wrote Static Pod manifest for a local etcd instance to "/etc/kubernetes/manifests/etcd.yaml"
[init] Waiting for the kubelet to boot up the control plane as Static Pods from directory "/etc/kubernetes/manifests"
[init] This often takes around a minute; or longer if the control plane images have to be pulled.
 
[apiclient] All control plane components are healthy after 26.502795 seconds
[uploadconfig] Storing the configuration used in ConfigMap "kubeadm-config" in the "kube-system" Namespace
[markmaster] Will mark node master as master by adding a label and a taint
[markmaster] Master master tainted and labelled with key/value: node-role.kubernetes.io/master=""
[bootstraptoken] Using token: 4bdbca.6e3531d0ec698d96
[bootstraptoken] Configured RBAC rules to allow Node Bootstrap tokens to post CSRs in order for nodes to get long term certificate credentials
[bootstraptoken] Configured RBAC rules to allow the csrapprover controller automatically approve CSRs from a Node Bootstrap Token
[bootstraptoken] Configured RBAC rules to allow certificate rotation for all node client certificates in the cluster
[bootstraptoken] Creating the "cluster-info" ConfigMap in the "kube-public" namespace
[addons] Applied essential addon: kube-dns
[addons] Applied essential addon: kube-proxy
 
Your Kubernetes master has initialized successfully!
 
To start using your cluster, you need to run (as a regular user):
 
  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config
 
You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
  http://kubernetes.io/docs/admin/addons/
 
You can now join any number of machines by running the following on each node
as root:
 
  kubeadm join --token 4bdbca.6e3531d0ec698d96 192.168.22.78:6443 --discovery-token-ca-cert-hash sha256:934dc12dff4fde78dd9ced37f0b3d3f4d92b128c25196b9ade7dc77b44d929d7
```

kubeadm init命令在/etc/kubernetes目录生成配置文件

1.初始化的参数：–pod-network-cidr是子网网段，–kubernetes-version 现在我们用的是1.8.2

2.中间有提到复制/etc/kubernetes/admin.conf到$HOME/.kube/config，是因为yum安装的kubectl命令通过此配置文件连接运行在docker里面的api接口

3.kubeadm join是node节点加入此机器所要执行的命令

如果中途卡主了，查看系统日志 less /var/log/messages，比如：

```
k8s.io/kubernetes/pkg/kubelet/kubelet.go:413: Failed to list *v1.Service: 
Get https://192.168.22.78:6443/api/v1/services?resourceVersion=0: 
dial tcp 192.168.22.78:6443: getsockopt: connection refused
```

```
# mkdir -p $HOME/.kube
# cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
# chown $(id -u):$(id -g) $HOME/.kube/config
# kubectl get nodes
NAME      STATUS     ROLES     AGE       VERSION
master    NotReady   master    17h        v1.8.2
```

### **calico组件安装**

解压压缩包，进入k8s_1.8.2/k8s_1.8.2_rpm/目录

```
# kubectl apply -f calico.yaml
configmap "calico-config" created
daemonset "calico-etcd" created
service "calico-etcd" created
daemonset "calico-node" created
deployment "calico-kube-controllers" created
deployment "calico-policy-controller" created
clusterrolebinding "calico-cni-plugin" created
clusterrole "calico-cni-plugin" created
serviceaccount "calico-cni-plugin" created
clusterrolebinding "calico-kube-controllers" created
clusterrole "calico-kube-controllers" created
serviceaccount "calico-kube-controllers" created
 
calico链接： https://docs.projectcalico.org/v2.6/getting-started/kubernetes/installation/hosted/kubeadm/1.6/calico.yaml
```

### **node节点配置**

设置hostname，一样的初始化系统配置，安装docker并启动，导入kubernetes images，启动kubelet服务

```
# systemctl enable kubelet && systemctl start kubelet
kubeadm join --token 4bdbca.6e3531d0ec698d96 192.168.22.78:6443 --discovery-token-ca-cert-hash sha256:934dc12dff4fde78dd9ced37f0b3d3f4d92b128c25196b9ade7dc77b44d929d7
[kubeadm] WARNING: kubeadm is in beta, please do not use it for production clusters.
[preflight] Running pre-flight checks
[discovery] Trying to connect to API Server "192.168.22.78:6443"
[discovery] Created cluster-info discovery client, requesting info from "https://192.168.22.78:6443"
[discovery] Requesting info from "https://192.168.22.78:6443" again to validate TLS against the pinned public key
[discovery] Cluster info signature and contents are valid and TLS certificate validates against pinned roots, will use API Server "192.168.22.78:6443"
[discovery] Successfully established connection with API Server "192.168.22.78:6443"
[bootstrap] Detected server version: v1.8.2
[bootstrap] The server supports the Certificates API (certificates.k8s.io/v1beta1)
 
Node join complete:
* Certificate signing request sent to master and response
  received.
* Kubelet informed of new secure connection details.
 
Run 'kubectl get nodes' on the master to see this machine join.
```

稍等查看node节点状态

```
# kubectl get nodes
NAME      STATUS    ROLES     AGE       VERSION
master    Ready     master    18h       v1.8.2
node      Ready     <none>    16h       v1.8.2
```

### **dashboard组件安装**

```
# kubectl apply -f k8s_1.8.2/k8s_1.8.2_yaml/kubernetes-dashboard.yaml 
serviceaccount "kubernetes-dashboard" created
role "kubernetes-dashboard-minimal" created
rolebinding "kubernetes-dashboard-minimal" created
deployment "kubernetes-dashboard" created
service "kubernetes-dashboard" created
# kubectl apply -f apply -f k8s_1.8.2/k8s_1.8.2_yaml/dashboard-admin.yaml
 
# nohup kubectl proxy --address='0.0.0.0' --port=80 --accept-hosts='^*$' &
 
dashboard链接：https://raw.githubusercontent.com/kubernetes/dashboard/master/src/deploy/alternative/kubernetes-dashboard.yaml
dashboard-admin链接：https://github.com/kubernetes/dashboard/wiki/Access-control#official-release
```

浏览器访问master主机ip，即显api接口列表,dashboard界面访问此链接：

http://master_ip/ui ，注：这个dashboard没有加入认证，直接登录

![kubeadm部署kubernetes 1.8离线安装绝对成功版 - 第1张](../images/2017/12/%E5%BE%AE%E4%BF%A1%E6%88%AA%E5%9B%BE_20171213105055.png)

因为80端口一般用于服务，所以dashboard中端口改为默认的8001，kubernetes-dashboard.yaml中Service服务下，spec–ports–port 这里改为8001

```
nohup kubectl proxy --address='0.0.0.0' --port=8001 --accept-hosts='^*$' &
```

浏览器访问http://master_IP:8001/ui

不过有出现过访问ui界面提示：

```
Error: 'malformed HTTP response "\x15\x03\x01\x00\x02\x02"'
Trying to reach: 'http://192.168.219.68:8443/'
```

试试访问 http://MASTER_IP:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview?namespace=default

### **常用命令**

```
kubectl get service
kubectl get nodes
kubectl get namespace
kubectl get pods -n kube-system
kubectl get pods -n kube-system -o wide
kubectl describe pods kubernetes-dashboard -n kube-system
kubectl delete pods,service -l kubernetes-dashboard -n kube-system
kubectl delete -f dashboard.yaml
kubectl get svc -o wide -n kube-system
kubectl get service --all-namespaces=true -o wide
kubectl delete svc kubernetes-dashboard -n kube-system
kubectl delete deploy kubernetes-dashboard -n kube-system
kubectl get pods --all-namespaces
kubectl get all -n kube-system
```

### **重置集群**

```
kubeadm reset
```

### **查看服务状态**

```
# kubectl get po -n kube-system
NAME                                       READY     STATUS    RESTARTS   AGE
calico-etcd-l7m4p                          1/1       Running   1          17h
calico-kube-controllers-685f8bc7fb-l89qq   1/1       Running   1          17h
calico-node-vcfd6                          2/2       Running   2          17h
calico-node-wrj2q                          2/2       Running   1          15h
etcd-master                                1/1       Running   2          17h
kube-apiserver-master                      1/1       Running   2          17h
kube-controller-manager-master             1/1       Running   2          17h
kube-dns-545bc4bfd4-s9btp                  3/3       Running   3          17h
kube-proxy-7wcjs                           1/1       Running   2          17h
kube-proxy-dbnz5                           1/1       Running   0          15h
kube-scheduler-master                      1/1       Running   1          17h
kubernetes-dashboard-7556d8744-b9mc7       1/1       Running   0          41m
 
# kubectl cluster-info
Kubernetes master is running at https://192.168.22.78:6443
KubeDNS is running at https://192.168.22.78:6443/api/v1/namespaces/kube-system/services/kube-dns/proxy
 
To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

安装配置如上述，如有问题，敬请留言

### **k8s 1.8集群配置**

0，需要3个master节点

```
/etc/hosts 文件新加如下：
192.168.78 master01
192.168.76 master02
192.168.77 master03
192.168.79 node
```

1，配置keepalived，参考[kubernetes1.9版本集群配置向导](http://bbotte.com/kvm-xen/kubernetes-1-9-version-cluster-configuration-wizard/)

2，kubeadm init初始化使用配置文件

```
# cat /etc/kubernetes/config.yaml
apiVersion: kubeadm.k8s.io/v1alpha1
kind: MasterConfiguration
networking:
  podSubnet: 10.244.0.0/16
kubernetesVersion: 1.8.2
api:
  advertiseAddress: "192.168.22.100"  #master节点keepalived配置的VIP
token: "4bdbca.6e3531d0ec698d96"
tokenTTL: "0s"
apiServerCertSANs:
- master01
- master02
- master03
- 192.168.22.78  #3个master节点
- 192.168.22.76
- 192.168.22.77
- 192.168.22.100  #master节点keepalived配置的VIP
- 127.0.0.1
```

kubeadm init –config /etc/kubernetes/config.yaml

3，复制master01配置文件到另外2个master节点

```
scp /etc/kubernetes/pki/* master02:/etc/kubernetes/pki/
scp /etc/kubernetes/config.yaml master02:/etc/kubernetes/
```

4，另外2个master节点进行初始化，kubeadm init –config /etc/kubernetes/config.yaml

附：

```
https://docs.projectcalico.org/v2.6/getting-started/kubernetes/installation/hosted/kubeadm/1.6/calico.yaml
calico.yaml
# Calico Version v2.6.3
# https://docs.projectcalico.org/v2.6/releases#v2.6.3
# This manifest includes the following component versions:
#   calico/node:v2.6.3
#   calico/cni:v1.11.1
#   calico/kube-controllers:v1.0.1
 
# This ConfigMap is used to configure a self-hosted Calico installation.
kind: ConfigMap
apiVersion: v1
metadata:
  name: calico-config
  namespace: kube-system
data:
  # The location of your etcd cluster.  This uses the Service clusterIP
  # defined below.
  etcd_endpoints: "http://10.96.232.136:6666"
 
  # Configure the Calico backend to use.
  calico_backend: "bird"
 
  # The CNI network configuration to install on each node.
  cni_network_config: |-
    {
        "name": "k8s-pod-network",
        "cniVersion": "0.1.0",
        "type": "calico",
        "etcd_endpoints": "__ETCD_ENDPOINTS__",
        "log_level": "info",
        "mtu": 1500,
        "ipam": {
            "type": "calico-ipam"
        },
        "policy": {
            "type": "k8s",
             "k8s_api_root": "https://__KUBERNETES_SERVICE_HOST__:__KUBERNETES_SERVICE_PORT__",
             "k8s_auth_token": "__SERVICEACCOUNT_TOKEN__"
        },
        "kubernetes": {
            "kubeconfig": "/etc/cni/net.d/__KUBECONFIG_FILENAME__"
        }
    }
 
---
 
# This manifest installs the Calico etcd on the kubeadm master.  This uses a DaemonSet
# to force it to run on the master even when the master isn't schedulable, and uses
# nodeSelector to ensure it only runs on the master.
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  name: calico-etcd
  namespace: kube-system
  labels:
    k8s-app: calico-etcd
spec:
  template:
    metadata:
      labels:
        k8s-app: calico-etcd
      annotations:
        # Mark this pod as a critical add-on; when enabled, the critical add-on scheduler
        # reserves resources for critical add-on pods so that they can be rescheduled after
        # a failure.  This annotation works in tandem with the toleration below.
        scheduler.alpha.kubernetes.io/critical-pod: ''
    spec:
      # Only run this pod on the master.
      tolerations:
      # this taint is set by all kubelets running `--cloud-provider=external`
      # so we should tolerate it to schedule the calico pods
      - key: node.cloudprovider.kubernetes.io/uninitialized
        value: "true"
        effect: NoSchedule
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      # Allow this pod to be rescheduled while the node is in "critical add-ons only" mode.
      # This, along with the annotation above marks this pod as a critical add-on.
      - key: CriticalAddonsOnly
        operator: Exists
      nodeSelector:
        node-role.kubernetes.io/master: ""
      hostNetwork: true
      containers:
        - name: calico-etcd
          image: quay.io/coreos/etcd:v3.1.10
          env:
            - name: CALICO_ETCD_IP
              valueFrom:
                fieldRef:
                  fieldPath: status.podIP
          command: ["/bin/sh","-c"]
          args: ["/usr/local/bin/etcd --name=calico --data-dir=/var/etcd/calico-data --advertise-client-urls=http://$CALICO_ETCD_IP:6666 --listen-client-urls=http://0.0.0.0:6666 --listen-peer-urls=http://0.0.0.0:6667"]
          volumeMounts:
            - name: var-etcd
              mountPath: /var/etcd
      volumes:
        - name: var-etcd
          hostPath:
            path: /var/etcd
 
---
 
# This manifest installs the Service which gets traffic to the Calico
# etcd.
apiVersion: v1
kind: Service
metadata:
  labels:
    k8s-app: calico-etcd
  name: calico-etcd
  namespace: kube-system
spec:
  # Select the calico-etcd pod running on the master.
  selector:
    k8s-app: calico-etcd
  # This ClusterIP needs to be known in advance, since we cannot rely
  # on DNS to get access to etcd.
  clusterIP: 10.96.232.136
  ports:
    - port: 6666
 
---
 
# This manifest installs the calico/node container, as well
# as the Calico CNI plugins and network config on
# each master and worker node in a Kubernetes cluster.
kind: DaemonSet
apiVersion: extensions/v1beta1
metadata:
  name: calico-node
  namespace: kube-system
  labels:
    k8s-app: calico-node
spec:
  selector:
    matchLabels:
      k8s-app: calico-node
  template:
    metadata:
      labels:
        k8s-app: calico-node
      annotations:
        # Mark this pod as a critical add-on; when enabled, the critical add-on scheduler
        # reserves resources for critical add-on pods so that they can be rescheduled after
        # a failure.  This annotation works in tandem with the toleration below.
        scheduler.alpha.kubernetes.io/critical-pod: ''
    spec:
      hostNetwork: true
      tolerations:
      # this taint is set by all kubelets running `--cloud-provider=external`
      # so we should tolerate it to schedule the calico pods
      - key: node.cloudprovider.kubernetes.io/uninitialized
        value: "true"
        effect: NoSchedule
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      # Allow this pod to be rescheduled while the node is in "critical add-ons only" mode.
      # This, along with the annotation above marks this pod as a critical add-on.
      - key: CriticalAddonsOnly
        operator: Exists
      serviceAccountName: calico-cni-plugin
      # Minimize downtime during a rolling upgrade or deletion; tell Kubernetes to do a "force
      # deletion": https://kubernetes.io/docs/concepts/workloads/pods/pod/#termination-of-pods.
      terminationGracePeriodSeconds: 0
      containers:
        # Runs calico/node container on each Kubernetes node.  This
        # container programs network policy and routes on each
        # host.
        - name: calico-node
          image: quay.io/calico/node:v2.6.3
          env:
            # The location of the Calico etcd cluster.
            - name: ETCD_ENDPOINTS
              valueFrom:
                configMapKeyRef:
                  name: calico-config
                  key: etcd_endpoints
            # Enable BGP.  Disable to enforce policy only.
            - name: CALICO_NETWORKING_BACKEND
              valueFrom:
                configMapKeyRef:
                  name: calico-config
                  key: calico_backend
            # Cluster type to identify the deployment type
            - name: CLUSTER_TYPE
              value: "kubeadm,bgp"
            # Set noderef for node controller.
            - name: CALICO_K8S_NODE_REF
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
            # Disable file logging so `kubectl logs` works.
            - name: CALICO_DISABLE_FILE_LOGGING
              value: "true"
            # Set Felix endpoint to host default action to ACCEPT.
            - name: FELIX_DEFAULTENDPOINTTOHOSTACTION
              value: "ACCEPT"
            # Configure the IP Pool from which Pod IPs will be chosen.
            - name: CALICO_IPV4POOL_CIDR
              value: "192.168.0.0/16"
            - name: CALICO_IPV4POOL_IPIP
              value: "always"
            # Disable IPv6 on Kubernetes.
            - name: FELIX_IPV6SUPPORT
              value: "false"
            # Set MTU for tunnel device used if ipip is enabled
            - name: FELIX_IPINIPMTU
              value: "1440"
            # Set Felix logging to "info"
            - name: FELIX_LOGSEVERITYSCREEN
              value: "info"
            # Auto-detect the BGP IP address.
            - name: IP
              value: ""
            - name: FELIX_HEALTHENABLED
              value: "true"
          securityContext:
            privileged: true
          resources:
            requests:
              cpu: 250m
          livenessProbe:
            httpGet:
              path: /liveness
              port: 9099
            periodSeconds: 10
            initialDelaySeconds: 10
            failureThreshold: 6
          readinessProbe:
            httpGet:
              path: /readiness
              port: 9099
            periodSeconds: 10
          volumeMounts:
            - mountPath: /lib/modules
              name: lib-modules
              readOnly: true
            - mountPath: /var/run/calico
              name: var-run-calico
              readOnly: false
        # This container installs the Calico CNI binaries
        # and CNI network config file on each node.
        - name: install-cni
          image: quay.io/calico/cni:v1.11.1
          command: ["/install-cni.sh"]
          env:
            # The location of the Calico etcd cluster.
            - name: ETCD_ENDPOINTS
              valueFrom:
                configMapKeyRef:
                  name: calico-config
                  key: etcd_endpoints
            # The CNI network config to install on each node.
            - name: CNI_NETWORK_CONFIG
              valueFrom:
                configMapKeyRef:
                  name: calico-config
                  key: cni_network_config
          volumeMounts:
            - mountPath: /host/opt/cni/bin
              name: cni-bin-dir
            - mountPath: /host/etc/cni/net.d
              name: cni-net-dir
      volumes:
        # Used by calico/node.
        - name: lib-modules
          hostPath:
            path: /lib/modules
        - name: var-run-calico
          hostPath:
            path: /var/run/calico
        # Used to install CNI.
        - name: cni-bin-dir
          hostPath:
            path: /opt/cni/bin
        - name: cni-net-dir
          hostPath:
            path: /etc/cni/net.d
 
---
 
# This manifest deploys the Calico Kubernetes controllers.
# See https://github.com/projectcalico/kube-controllers
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: calico-kube-controllers
  namespace: kube-system
  labels:
    k8s-app: calico-kube-controllers
spec:
  # The controllers can only have a single active instance.
  replicas: 1
  strategy:
    type: Recreate
  template:
    metadata:
      name: calico-kube-controllers
      namespace: kube-system
      labels:
        k8s-app: calico-kube-controllers
      annotations:
        # Mark this pod as a critical add-on; when enabled, the critical add-on scheduler
        # reserves resources for critical add-on pods so that they can be rescheduled after
        # a failure.  This annotation works in tandem with the toleration below.
        scheduler.alpha.kubernetes.io/critical-pod: ''
    spec:
      # The controllers must run in the host network namespace so that
      # it isn't governed by policy that would prevent it from working.
      hostNetwork: true
      tolerations:
      # this taint is set by all kubelets running `--cloud-provider=external`
      # so we should tolerate it to schedule the calico pods
      - key: node.cloudprovider.kubernetes.io/uninitialized
        value: "true"
        effect: NoSchedule
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      # Allow this pod to be rescheduled while the node is in "critical add-ons only" mode.
      # This, along with the annotation above marks this pod as a critical add-on.
      - key: CriticalAddonsOnly
        operator: Exists
      serviceAccountName: calico-kube-controllers
      containers:
        - name: calico-kube-controllers
          image: quay.io/calico/kube-controllers:v1.0.1
          env:
            # The location of the Calico etcd cluster.
            - name: ETCD_ENDPOINTS
              valueFrom:
                configMapKeyRef:
                  name: calico-config
                  key: etcd_endpoints
            # The location of the Kubernetes API.  Use the default Kubernetes
            # service for API access.
            - name: K8S_API
              value: "https://kubernetes.default:443"
            # Choose which controllers to run.
            - name: ENABLED_CONTROLLERS
              value: policy,profile,workloadendpoint,node
            # Since we're running in the host namespace and might not have KubeDNS
            # access, configure the container's /etc/hosts to resolve
            # kubernetes.default to the correct service clusterIP.
            - name: CONFIGURE_ETC_HOSTS
              value: "true"
 
---
 
# This deployment turns off the old "policy-controller". It should remain at 0 replicas, and then
# be removed entirely once the new kube-controllers deployment has been deployed above.
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: calico-policy-controller
  namespace: kube-system
  labels:
    k8s-app: calico-policy-controller
spec:
  # Turn this deployment off in favor of the kube-controllers deployment above.
  replicas: 0
  strategy:
    type: Recreate
  template:
    metadata:
      name: calico-policy-controller
      namespace: kube-system
      labels:
        k8s-app: calico-policy-controller
    spec:
      hostNetwork: true
      serviceAccountName: calico-kube-controllers
      containers:
        - name: calico-policy-controller
          image: quay.io/calico/kube-controllers:v1.0.1
          env:
            - name: ETCD_ENDPOINTS
              valueFrom:
                configMapKeyRef:
                  name: calico-config
                  key: etcd_endpoints
 
---
 
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: calico-cni-plugin
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: calico-cni-plugin
subjects:
- kind: ServiceAccount
  name: calico-cni-plugin
  namespace: kube-system
 
---
 
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: calico-cni-plugin
rules:
  - apiGroups: [""]
    resources:
      - pods
      - nodes
    verbs:
      - get
 
---
 
apiVersion: v1
kind: ServiceAccount
metadata:
  name: calico-cni-plugin
  namespace: kube-system
 
---
 
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: calico-kube-controllers
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: calico-kube-controllers
subjects:
- kind: ServiceAccount
  name: calico-kube-controllers
  namespace: kube-system
 
---
 
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: calico-kube-controllers
rules:
  - apiGroups:
    - ""
    - extensions
    resources:
      - pods
      - namespaces
      - networkpolicies
      - nodes
    verbs:
      - watch
      - list
 
---
 
apiVersion: v1
kind: ServiceAccount
metadata:
  name: calico-kube-controllers
  namespace: kube-system
```

```
https://raw.githubusercontent.com/kubernetes/dashboard/master/src/deploy/alternative/kubernetes-dashboard.yaml
kubernetes-dashboard.yaml
# Copyright 2017 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
 
 
# Configuration to deploy release version of the Dashboard UI compatible with
# Kubernetes 1.8.
#
# Example usage: kubectl create -f <this_file>
 
# ------------------- Dashboard Service Account ------------------- #
 
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kube-system
 
---
# ------------------- Dashboard Role & Role Binding ------------------- #
 
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: kubernetes-dashboard-minimal
  namespace: kube-system
rules:
  # Allow Dashboard to create 'kubernetes-dashboard-key-holder' secret.
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["create"]
  # Allow Dashboard to create 'kubernetes-dashboard-settings' config map.
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["create"]
  # Allow Dashboard to get, update and delete Dashboard exclusive secrets.
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["kubernetes-dashboard-key-holder"]
  verbs: ["get", "update", "delete"]
  # Allow Dashboard to get and update 'kubernetes-dashboard-settings' config map.
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["kubernetes-dashboard-settings"]
  verbs: ["get", "update"]
  # Allow Dashboard to get metrics from heapster.
- apiGroups: [""]
  resources: ["services"]
  resourceNames: ["heapster"]
  verbs: ["proxy"]
- apiGroups: [""]
  resources: ["services/proxy"]
  resourceNames: ["heapster", "http:heapster:", "https:heapster:"]
  verbs: ["get"]
 
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: kubernetes-dashboard-minimal
  namespace: kube-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: kubernetes-dashboard-minimal
subjects:
- kind: ServiceAccount
  name: kubernetes-dashboard
  namespace: kube-system
 
---
# ------------------- Dashboard Deployment ------------------- #
 
kind: Deployment
apiVersion: apps/v1beta2
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kube-system
spec:
  replicas: 1
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      k8s-app: kubernetes-dashboard
  template:
    metadata:
      labels:
        k8s-app: kubernetes-dashboard
    spec:
      containers:
      - name: kubernetes-dashboard
        # image: gcr.io/google_containers/kubernetes-dashboard-amd64:v1.8.0
        image: index.tenxcloud.com/jimmy/kubernetes-dashboard-amd64:v1.8.0
        ports:
        - containerPort: 9090
          protocol: TCP
        args:
          # Uncomment the following line to manually specify Kubernetes API server Host
          # If not specified, Dashboard will attempt to auto discover the API server and connect
          # to it. Uncomment only if the default does not work.
          # - --apiserver-host=http://my-address:port
        volumeMounts:
          # Create on-disk volume to store exec logs
        - mountPath: /tmp
          name: tmp-volume
        livenessProbe:
          httpGet:
            path: /
            port: 9090
          initialDelaySeconds: 30
          timeoutSeconds: 30
      volumes:
      - name: tmp-volume
        emptyDir: {}
      serviceAccountName: kubernetes-dashboard
      # Comment the following tolerations if Dashboard must not be deployed on master
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
 
---
# ------------------- Dashboard Service ------------------- #
 
kind: Service
apiVersion: v1
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kube-system
spec:
  ports:
  - port: 80
    targetPort: 9090
  selector:
    k8s-app: kubernetes-dashboard
```

```
https://github.com/kubernetes/dashboard/wiki/Access-control#official-release
dashboard-admin.yaml
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: kubernetes-dashboard
  labels:
    k8s-app: kubernetes-dashboard
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: kubernetes-dashboard
  namespace: kube-system
```

kubernetes dashboard界面参考

[https://github.com/kubernetes/dashboard/wiki/Accessing-Dashboard—1.7.X-and-above](https://github.com/kubernetes/dashboard/wiki/Accessing-Dashboard---1.7.X-and-above)

2017年12月12日 于 [linux工匠](https://bbotte.github.io/) 发表