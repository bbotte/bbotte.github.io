## kubernetes 1.20版本集群安装



### 环境版本

| 说明      | 版本            |
| --------- | --------------- |
| 系统      | CentOS 7.8      |
| k8s       | 1.22.2          |
| 网络插件  | flannel v0.15.0 |
| etcd      | 3.4.13          |
| docker-ce | 20.10.8         |

k8s api的VIP使用keepalived，

### 系统参数调整

1，定义master和node节点名称，并更新hosts文件，例如k8s-master01节点

```
hostnamectl --static set-hostname k8s-master01
exec $SHELL
cat /etc/hosts
192.168.3.9     k8s-master01 etcd1
192.168.3.10    k8s-master02 etcd2
192.168.3.11    k8s-master03 etcd3
192.168.3.13    k8s-worker01
```

192.168.3.12 为 k8s api的VIP

更改系统参数，避免初始化集群提示bridge-nf-call-iptables和swap

```
[ERROR FileContent--proc-sys-net-bridge-bridge-nf-call-iptables]: /proc/sys/net/bridge/bridge-nf-call-iptables contents are not set to 1
[ERROR FileContent--proc-sys-net-ipv4-ip_forward]: /proc/sys/net/ipv4/ip_forward contents are not set to 1
```

```
swapoff -a
sed -i 's/.*swap.*/#&/' /etc/fstab
systemctl stop firewalld
systemctl disable firewalld
sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config 
setenforce 0
iptables -P FORWARD ACCEPT
cat <<EOF >> /etc/sysctl.conf
net.ipv4.ip_forward=1
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
vm.swappiness = 0
EOF
sysctl -p
```

下面只在master节点执行

```
cat > /etc/sysconfig/modules/ipvs.modules <<EOF
#!/bin/bash
modprobe -- ip_vs
modprobe -- ip_vs_rr
modprobe -- ip_vs_wrr
modprobe -- ip_vs_sh
modprobe -- nf_conntrack_ipv4
EOF
chmod 755 /etc/sysconfig/modules/ipvs.modules && bash /etc/sysconfig/modules/ipvs.modules && lsmod | grep -e ip_vs -e nf_conntrack_ipv4
sysctl -p
```

keepalived安装参考,<https://bbotte.github.io/virtualization/kubernetes_cluster_install_1-13-3>，设置kube_api_VIP(IP和主机名根据实际情况改动)，把keepalived先安装好

生成etcd和k8s集群所用的证书参考 ,<https://bbotte.github.io/virtualization/kubernetes_cluster_install_1-13-3>，生成证书(仅需其中一台，在master1操作)

### etcd集群

```
wget https://github.com/etcd-io/etcd/releases/download/v3.4.14/etcd-v3.4.14-linux-amd64.tar.gz
tar -xf etcd-v3.4.14-linux-amd64.tar.gz
cp etcd-v3.4.14-linux-amd64/etcd etcd-v3.4.14-linux-amd64/etcdctl /usr/bin
mkdir /etc/etcd

cat > /etc/etcd/etcd.conf.yml <<EOF
name: 'etcd1'               #这里改
data-dir: /var/lib/etcd/data
wal-dir: /var/lib/etcd/wal
snapshot-count: 100000
heartbeat-interval: 100
election-timeout: 1000
quota-backend-bytes: 0
listen-peer-urls: https://192.168.3.9:2380        #下面几个ip要改
listen-client-urls: https://192.168.3.9:2379,http://127.0.0.1:2379
max-snapshots: 5
max-wals: 5
cors:
initial-advertise-peer-urls: https://192.168.3.9:2380
advertise-client-urls: https://192.168.3.9:2379
discovery:
discovery-fallback: 'proxy'
discovery-proxy:
discovery-srv:
initial-cluster: etcd1=https://192.168.3.9:2380,etcd2=https://192.168.3.10:2380,etcd3=https://192.168.3.11:2380
initial-cluster-token: 'etcd-cluster'
initial-cluster-state: 'new'
strict-reconfig-check: false
enable-v2: false
enable-pprof: false
proxy: 'off'
proxy-failure-wait: 5000
proxy-refresh-interval: 30000
proxy-dial-timeout: 1000
proxy-write-timeout: 5000
proxy-read-timeout: 0
client-transport-security:
  cert-file: /etc/etcd/ssl/etcd.pem
  key-file: /etc/etcd/ssl/etcd-key.pem
  client-cert-auth: true
  trusted-ca-file: /etc/etcd/ssl/ca.pem
  auto-tls: false
peer-transport-security:
  cert-file: /etc/etcd/ssl/etcd.pem
  key-file: /etc/etcd/ssl/etcd-key.pem
  client-cert-auth: true
  trusted-ca-file: /etc/etcd/ssl/ca.pem
  auto-tls: false
debug: false
logger: capnslog
log-outputs: [stderr]
force-new-cluster: false
auto-compaction-mode: periodic
auto-compaction-retention: "1"
EOF

cat > /usr/lib/systemd/system/etcd.service <<EOF
[Unit]
Description=Etcd Server
After=network.target
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
WorkingDirectory=/var/lib/etcd/
User=etcd
#  set GOMAXPROCS to number of processors
ExecStart=/bin/bash -c "GOMAXPROCS=$(nproc) /usr/bin/etcd --config-file /etc/etcd/etcd.conf.yml"
Restart=on-failure
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

chmod 644 /etc/etcd/ssl/*
mkdir -p /var/lib/etcd/
chmod 700 /var/lib/etcd
getent group etcd >/dev/null || groupadd -r etcd
getent passwd etcd >/dev/null || useradd -r -g etcd -d /var/lib/etcd -s /sbin/nologin -c "etcd user" etcd
chown etcd.etcd -R /var/lib/etcd/
systemctl daemon-reload
systemctl enable etcd
systemctl start etcd
export ETCDCTL_API=3
cat >> /etc/profile.d/etcd.sh <<EOF
export ETCDCTL_API=3
EOF
systemctl enable etcd
systemctl start etcd
```

参考 https://bbotte.github.io/service_config/etcd-v3.4_install/etcd-install

### docker安装

https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/centos/7/x86_64/stable/Packages/

下载docker rpm安装即可

```
cat <<EOF>> /etc/docker/daemon.json
"exec-opts": ["native.cgroupdriver=systemd"]
EOF
```

这里是因为kubelet用的是docker systemd，而不是cgroup

```
kubelet "Failed to run kubelet" err="failed to run Kubelet: misconfiguration: kubelet cgroup driver: \"systemd\" is different from docker cgroup driver: \"cgroupfs\""
Unit kubelet.service entered failed state
```



### kubeadm编译

编译kubeadm延长证书时间需要go环境，参考 https://bbotte.github.io/virtualization/kubernetes-cluster-certificate-created-by-kubeadm-expires-renewal  编译kubeadm

```
wget https://github.com/kubernetes/kubernetes/archive/refs/tags/v1.22.2.zip
解压后进入k8s代码目录
vim vendor/k8s.io/client-go/util/cert/cert.go
38 const duration365d = time.Hour * 24 * 365 * 10
97         maxAge := time.Hour * 24 * 365 * 10          // one year self-signed certs

vim staging/src/k8s.io/client-go/util/cert/cert.go
 38 const duration365d = time.Hour * 24 * 365 * 10
 97         maxAge := time.Hour * 24 * 365 * 10          // one year self-signed certs

vim cmd/kubeadm/app/constants/constants.go
48         CertificateValidity = time.Hour * 24 * 365 * 10

make all WHAT=cmd/kubeadm GOFLAGS=-v
ls  _output/local/bin/linux/amd64/kubeadm
```



### 安装kubelet、kubeadm、kubectl

```
cat > /etc/yum.repos.d/kubernetes.repo <<EOF
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
EOF
yum install -y kubelet-1.22.2 kubeadm-1.22.2 kubectl-1.22.2 --disableexcludes=kubernetes
systemctl enable --now kubelet
```



### 初始化k8s集群并添加节点

```
cat > initk8s.yaml <<EOF
apiVersion: kubeadm.k8s.io/v1beta3
bootstrapTokens:
- groups:
  - system:bootstrappers:kubeadm:default-node-token
  token: pnfw5a.1111222200001111 # kubeadm token generate
  ttl: 108h0m0s
  usages:
  - signing
  - authentication
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: 192.168.3.12 #api VIP
  bindPort: 6443
nodeRegistration:
  criSocket: /var/run/dockershim.sock
  name: k8s-master01                  #master1 名字
  taints:
  - effect: NoSchedule
    key: node-role.kubernetes.io/master
---
apiServer:
  timeoutForControlPlane: 4m0s
  CertSANs:
  - etcd1              #etcd name
  - etcd2
  - etcd3
  - 192.168.3.9         #master IP
  - 192.168.3.10
  - 192.168.3.11
  - 192.168.3.12       #api VIP
  - 127.0.0.1
  - kubernetes
  - kubernetes.default
  - kubernetes.default.svc
  - kubernetes.default.svc.cluster
  - kubernetes.default.svc.cluster.local
  - 10.244.0.1
  - 10.96.0.1
apiVersion: kubeadm.k8s.io/v1beta3
certificatesDir: /etc/kubernetes/pki
clusterName: kubernetes
controlPlaneEndpoint: "192.168.3.12:6443"  #api VIP
controllerManager: {}
dns: {}
etcd:
  external:
    endpoints:
    - https://192.168.3.9:2379    #three etcd node
    - https://192.168.3.10:2379    #three etcd node
    - https://192.168.3.11:2379    #three etcd node
    caFile: /etc/kubernetes/ssl/ca.pem    #same as /etc/etcd/etcd.conf ca
    certFile: /etc/kubernetes/ssl/etcd.pem 
    keyFile: /etc/kubernetes/ssl/etcd-key.pem
imageRepository: registry.cn-hangzhou.aliyuncs.com/google_containers #your define docker registry
kind: ClusterConfiguration
kubernetesVersion: v1.22.2
networking:
  dnsDomain: cluster.local
  podSubnet: "10.244.0.0/17"   #pod ip address segment,every server has a ip segment, this network segment supports up to 127 hosts.
  serviceSubnet: 10.96.0.0/19 #service ip address segment,this network segment supports up to 8190 services.
scheduler: {}
---
EOF
```

使用上面编译的kubeadm初始化集群

```
kubeadm init --config initk8s.yaml 
[init] Using Kubernetes version: v1.22.2
[preflight] Running pre-flight checks
[preflight] Pulling images required for setting up a Kubernetes cluster
[preflight] This might take a minute or two, depending on the speed of your internet connection
[preflight] You can also perform this action in beforehand using 'kubeadm config images pull'
[certs] Using certificateDir folder "/etc/kubernetes/pki"
[certs] Using existing ca certificate authority
[certs] Using existing apiserver certificate and key on disk
[certs] Using existing apiserver-kubelet-client certificate and key on disk
[certs] Using existing front-proxy-ca certificate authority
[certs] Using existing front-proxy-client certificate and key on disk
[certs] External etcd mode: Skipping etcd/ca certificate authority generation
[certs] External etcd mode: Skipping etcd/server certificate generation
[certs] External etcd mode: Skipping etcd/peer certificate generation
[certs] External etcd mode: Skipping etcd/healthcheck-client certificate generation
[certs] External etcd mode: Skipping apiserver-etcd-client certificate generation
[certs] Using the existing "sa" key
[kubeconfig] Using kubeconfig folder "/etc/kubernetes"
[kubeconfig] Writing "admin.conf" kubeconfig file
[kubeconfig] Writing "kubelet.conf" kubeconfig file
[kubeconfig] Writing "controller-manager.conf" kubeconfig file
[kubeconfig] Writing "scheduler.conf" kubeconfig file
[kubelet-start] Writing kubelet environment file with flags to file "/var/lib/kubelet/kubeadm-flags.env"
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
[kubelet-start] Starting the kubelet

[control-plane] Using manifest folder "/etc/kubernetes/manifests"
[control-plane] Creating static Pod manifest for "kube-apiserver"
[control-plane] Creating static Pod manifest for "kube-controller-manager"
[control-plane] Creating static Pod manifest for "kube-scheduler"
[wait-control-plane] Waiting for the kubelet to boot up the control plane as static Pods from directory "/etc/kubernetes/manifests". This can take up to 4m0s

[kubelet-check] Initial timeout of 40s passed.
[apiclient] All control plane components are healthy after 200.027078 seconds
[upload-config] Storing the configuration used in ConfigMap "kubeadm-config" in the "kube-system" Namespace
[kubelet] Creating a ConfigMap "kubelet-config-1.22" in namespace kube-system with the configuration for the kubelets in the cluster
[upload-certs] Skipping phase. Please see --upload-certs
[mark-control-plane] Marking the node k8s-master02 as control-plane by adding the labels: [node-role.kubernetes.io/master(deprecated) node-role.kubernetes.io/control-plane node.kubernetes.io/exclude-from-external-load-balancers]
[mark-control-plane] Marking the node k8s-master02 as control-plane by adding the taints [node-role.kubernetes.io/master:NoSchedule]
[bootstrap-token] Using token: pnfw5z.o3v74cqgrwljqgr8
[bootstrap-token] Configuring bootstrap tokens, cluster-info ConfigMap, RBAC Roles
[bootstrap-token] configured RBAC rules to allow Node Bootstrap tokens to get nodes
[bootstrap-token] configured RBAC rules to allow Node Bootstrap tokens to post CSRs in order for nodes to get long term certificate credentials
[bootstrap-token] configured RBAC rules to allow the csrapprover controller automatically approve CSRs from a Node Bootstrap Token
[bootstrap-token] configured RBAC rules to allow certificate rotation for all node client certificates in the cluster
[bootstrap-token] Creating the "cluster-info" ConfigMap in the "kube-public" namespace
[kubelet-finalize] Updating "/etc/kubernetes/kubelet.conf" to point to a rotatable kubelet client certificate and key
[addons] Applied essential addon: CoreDNS
[addons] Applied essential addon: kube-proxy

Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

Alternatively, if you are the root user, you can run:

  export KUBECONFIG=/etc/kubernetes/admin.conf

You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
  https://kubernetes.io/docs/concepts/cluster-administration/addons/

You can now join any number of control-plane nodes by copying certificate authorities
and service account keys on each node and then running the following as root:

  kubeadm join 192.168.3.12:6443 --token pnfw5a.1111222200001111 \
	--discovery-token-ca-cert-hash sha256:cc7e8f0481a40f06e1d12363f9a5052ce9443fb2355a37fef991e9c56f76bd71 \
	--control-plane 

Then you can join any number of worker nodes by running the following on each as root:

kubeadm join 192.168.3.12:6443 --token pnfw5a.1111222200001111 \
	--discovery-token-ca-cert-hash sha256:cc7e8f0481a40f06e1d12363f9a5052ce9443fb2355a37fef991e9c56f76bd71 

```

这里已经有master节点的添加方式，直接添加master节点和node节点就行

查看证书时间

```
cd /etc/kubernetes/pki/
for i in *.crt;do echo $i; openssl x509 -in $i -text -noout|egrep "Not Before|Not After";echo "-----------";done
```

让人奇怪的是kubelet一直提示说coredns要使用flannel的env文件，如果使用其他的网络插件，比如kube-route，那么coredns还不能启动，必须手动配置/run/flannel/subnet.env，这个文件重启后即消失

```
k8s-master01 kubelet: "Error adding pod to network" err="open /run/flannel/subnet.env: no such file or directory" pod="kube-system/coredns-7d89d9b6b8-z4nzr" podSandboxID={Type:docker ID:} podNetnsPath="/proc/3652/ns/net" networkType="flannel" networkName="cbr0"
```

所以接下来安装flannel网络插件



### 安装flannel

flannel文件 https://github.com/flannel-io/flannel/blob/master/Documentation/kube-flannel.yml

kubectl get po -n kube-system  查看组件状态

```
# kubectl get no
NAME           STATUS   ROLES                  AGE    VERSION
k8s-master01   Ready    control-plane,master   17h    v1.22.2
k8s-master02   Ready    control-plane,master   16h    v1.22.2
k8s-master03   Ready    control-plane,master   16h    v1.22.2
k8s-worker01   Ready    <none>                 112m   v1.22.2
k8s-worker02   Ready    <none>                 42s    v1.22.2
k8s-worker03   Ready    <none>                 14s    v1.22.2

[root@k8s-master01 tmp]# kubectl edit deploy/coredns -n kube-system
deployment.apps/coredns edited
[root@k8s-master01 tmp]# kubectl get po -n kube-system 

```



