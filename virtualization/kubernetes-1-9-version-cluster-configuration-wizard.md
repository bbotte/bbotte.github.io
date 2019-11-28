# kubernetes1.9版本集群配置文档

1. 说明
2. 版本号
3. 初始化系统
4. 配置keepalived
5. 生成证书
6. etcd集群创建
7. 安装docker服务
8. kubernetes master节点操作
9. 配置kube-rouer
10. 扩展其他主节点
11. 配置kubernetes node节点
12. k8s1.9版本的dashboard界面
13. DNS使用默认的kube-dns
14. 遇到的错误

### 说明

使用kubeadm创建kubernetes环境是单个节点，需要对kube-api做高可用，这里使用keepalived对3个master节点kubernetes api做高可用，etcd也部署到3台master节点。网络使用CoreDNS+kube-router，随后再使用kube-proxy，以便你还不熟悉coredns和kube-route

kube-router取代kube-proxy,用lvs做svc负载均衡
coredns取代kube-dns，DNS更稳定，也可以看github上我写的kubernetes集群安装文档

https://github.com/bbotte/bbotte.github.io/virtualization/kubernetes_cluster_install_1.9.4

```
主机         IP      
k8smaster01  192.168.0.230
k8smaster02  192.168.0.231
k8smaster03  192.168.0.232
k8snode01    192.168.0.233
k8s api VIP  192.168.0.238
```

### 版本号

```
docker: 17.03.2-ce
OS: CentOS Linux release 7.4.1708
kubernetes: 1.9.4
etcdctl: 3.2.15
Keepalived: v1.3.5
 
[root@k8smaster01 ~]# docker images
REPOSITORY                                               TAG                 IMAGE ID            CREATED             SIZE
gcr.io/google_containers/kube-proxy-amd64                v1.9.4              119ae3dc765b        3 days ago          109 MB
gcr.io/google_containers/kube-scheduler-amd64            v1.9.4              897eabbc86ac        3 days ago          62.9 MB
gcr.io/google_containers/kube-apiserver-amd64            v1.9.4              3945a0b35e33        3 days ago          212 MB
gcr.io/google_containers/kube-controller-manager-amd64   v1.9.4              35c62345e5ac        3 days ago          139 MB
busybox                                                  latest              f6e427c148a7        2 weeks ago         1.15 MB
cloudnativelabs/kube-router                              latest              03dcb0d528f0        4 weeks ago         88.1 MB
coredns/coredns                                          1.0.1               58d63427cdea        3 months ago        45.1 MB
gcr.io/google_containers/k8s-dns-sidecar-amd64           1.14.7              db76ee297b85        4 months ago        42 MB
gcr.io/google_containers/k8s-dns-kube-dns-amd64          1.14.7              5d049a8c4eec        4 months ago        50.3 MB
gcr.io/google_containers/k8s-dns-dnsmasq-nanny-amd64     1.14.7              5feec37454f4        4 months ago        40.9 MB
gcr.io/google_containers/pause-amd64                     3.0                 99e59f495ffa        22 months ago       747 kB
```

下载链接

度娘网盘：https://pan.baidu.com/s/14kBym3dnBInqX73aZFW3ZA 密码：0r8i

docker download

```
https://download.docker.com/linux/centos/7/x86_64/stable/Packages/
```

etcd download

```
http://mirror.centos.org/centos/7/extras/x86_64/Packages/etcd-3.2.15-1.el7.x86_64.rpm
```

kubeadm、kubelet、kubectl、kubernetes-cni可以在国外云主机

```
更改/etc/yum.conf
keepcache=1
metadata_expire=9m
然后
yum install kubeadm-1.9.4-0 kubectl-1.9.4-0 kubelet-1.9.4-0
yum安装的文件会缓存到此目录：
/var/cache/yum/x86_64/7/kubernetes/packages
```

至于gcr.io/google_containers的docker包，docker pull image:latest拉下来，再docker save -o image.tar保存，拖到本地主机导入docker load < image.tar

### 初始化系统

```
hostnamectl --static set-hostname k8smaster01
exec $SHELL
cat <<EOF >> /etc/hosts
192.168.0.230 k8smaster01
192.168.0.231 k8smaster02
192.168.0.232 k8smaster03
192.168.0.233 k8snode01
EOF
swapoff -a
sed -i 's/.*swap.*/#&/' /etc/fstab
systemctl stop firewalld
systemctl disable firewalld
sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config 
setenforce 0
iptables -P FORWARD ACCEPT
yum install -y epel-release vim vim-enhanced wget lrzsz unzip ntpdate sysstat dstat wget mlocate mtr lsof iotop bind-tools git net-tools
timedatectl set-timezone Asia/Shanghai
ntpdate ntp1.aliyun.com
rm -f /etc/localtime
ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
systemctl restart rsyslog
echo 'export HISTTIMEFORMAT="%m/%d %T "' >> ~/.bashrc
source ~/.bashrc
cat  >> /etc/security/limits.conf << EOF
* soft nproc 65535
* hard nproc 65535
* soft nofile 65535
* hard nofile 65535
EOF
echo "ulimit -SHn 65535" >> /etc/profile
echo "ulimit -SHn 65535" >> /etc/rc.local
ulimit -SHn 65535
sed -i 's/4096/10240/' /etc/security/limits.d/20-nproc.conf
modprobe ip_conntrack
modprobe br_netfilter
cat >> /etc/rc.d/rc.local <<EOF
modprobe ip_conntrack
modprobe br_netfilter
EOF
chmod 744 /etc/rc.d/rc.local
cat <<EOF >>  /etc/sysctl.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
vm.swappiness = 0
vm.overcommit_memory=1
vm.panic_on_oom=0
kernel/panic=10
kernel/panic_on_oops=1
kernel.pid_max = 4194303
vm.max_map_count = 655350
fs.aio-max-nr = 524288
fs.file-max = 6590202
EOF
sysctl -p /etc/sysctl.conf
/sbin/sysctl -p
```

### 配置keepalived

```
# yum install keepalived ipvsadm -y
# cat /etc/keepalived/keepalived.conf
! Configuration File for keepalived
 
global_defs {
   notification_email {
      bbotte@163.com
   }
   router_id LVS_k8s
}
 
vrrp_script CheckK8sMaster {
    script "curl -k https://127.0.0.1:6443/api"
    interval 3
    timeout 9
    fall 3
    rise 3
}
 
vrrp_instance VI_1 {
    state MASTER            #MASTER/BACKUP
    interface ens192        #网卡名称
    virtual_router_id 51
    priority 100            #权重,配置不同数值，另2台为99,98
    advert_int 1
    # local host ip
    mcast_src_ip 192.168.0.230
    authentication {
        auth_type PASS
        auth_pass bbotte_k8s
    }
    unicast_peer {
        #对方的ip
        192.168.0.231
        192.168.0.232
    }
    virtual_ipaddress {
        192.168.0.238/24
    }
    track_script {
        CheckK8sMaster    
    }
}
 
# systemctl enable keepalived && systemctl restart keepalived
# yum install ipvsadm -y
# ipvsadm -Ln
```

ip a 查看主机的VIP是否绑定

### 生成证书

TLS证书用于etcd和kubernetes通信间加密，使用sfss工具来生成证书

```
wget https://pkg.cfssl.org/R1.2/cfssl_linux-amd64
wget https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
wget https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64
mv cfssl_linux-amd64 cfssl
mv cfssljson_linux-amd64 cfssljson
mv cfssl-certinfo_linux-amd64 cfssl-certinfo
mv cfssl* /usr/bin/
chmod +x /usr/bin/cfssl*
```

创建配置文件

```
# cat etcd-csr.json 
{
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "O": "etcd",
      "OU": "etcd Security",
      "L": "Beijing",
      "ST": "Beijing",
      "C": "CN"
    }
  ],
  "CN": "etcd",
  "hosts": [
    "127.0.0.1",
    "192.168.0.230",
    "192.168.0.231",
    "192.168.0.232",
    "192.168.0.238"
  ]
}
```

```
# cat etcd-gencert.json 
{
  "signing": {
    "default": {
        "usages": [
          "signing",
          "key encipherment",
          "server auth",
          "client auth"
        ],
        "expiry": "87600h"
    }
  }
}
```

```
# cat etcd-root-ca-csr.json 
{
  "key": {
    "algo": "rsa",
    "size": 4096
  },
  "names": [
    {
      "O": "etcd",
      "OU": "etcd Security",
      "L": "Beijing",
      "ST": "Beijing",
      "C": "CN"
    }
  ],
  "ca": {
    "expiry": "87600h"
  }
}
```

signing：表示该证书可用于签名其它证书
server auth：表示 client 可以用该 CA 对 server 提供的证书进行验证
client auth：表示 server 可以用该 CA 对 client 提供的证书进行验证
“CN”：Common Name，kube-apiserver 从证书中提取该字段作为请求的用户名 (User Name)，浏览器使用该字段验证网站是否合法
“O”：Organization，kube-apiserver 从证书中提取该字段作为请求用户所属的组 (Group)

生成证书

```
# cfssl gencert --initca=true etcd-root-ca-csr.json | cfssljson --bare ca
2018/03/15 18:41:32 [INFO] generating a new CA key and certificate from CSR
2018/03/15 18:41:32 [INFO] generate received request
2018/03/15 18:41:32 [INFO] received CSR
2018/03/15 18:41:32 [INFO] generating key: rsa-4096
2018/03/15 18:41:36 [INFO] encoded CSR
2018/03/15 18:41:36 [INFO] signed certificate with serial number 158304709925836637679572622010720113566389454971
# cfssl gencert --ca ca.pem --ca-key ca-key.pem --config etcd-gencert.json etcd-csr.json | cfssljson --bare etcd
2018/03/15 18:41:39 [INFO] generate received request
2018/03/15 18:41:39 [INFO] received CSR
2018/03/15 18:41:39 [INFO] generating key: rsa-2048
2018/03/15 18:41:39 [INFO] encoded CSR
2018/03/15 18:41:39 [INFO] signed certificate with serial number 490341771217690873586329693456356423605999635854
2018/03/15 18:41:39 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").
 
# scp etcd-key.pem etcd.pem ca.pem 192.168.0.230:/etc/etcd/ssl
```

/etc/etcd/ssl目录手动创建，并把生成的证书推送到3个master节点

### etcd集群创建

安装etcd的rpm包即可，修改etcd默认配置如下

```
# cat /etc/etcd/etcd.conf 
#[Member]
#ETCD_CORS=""
#etcd数据存储目录
ETCD_DATA_DIR="/var/lib/etcd/"         
#ETCD_WAL_DIR=""
#更改为本机IP
ETCD_LISTEN_PEER_URLS="https://192.168.0.230:2380" 
#更改为本机IP
ETCD_LISTEN_CLIENT_URLS="https://192.168.0.230:2379,http://127.0.0.1:2379"
#ETCD_MAX_SNAPSHOTS="5"
#ETCD_MAX_WALS="5"
#一个名字而已，和下面ETCD_INITIAL_CLUSTER变量中参数对应
ETCD_NAME="etcd01"              
#ETCD_SNAPSHOT_COUNT="100000"
#ETCD_HEARTBEAT_INTERVAL="100"
#ETCD_ELECTION_TIMEOUT="1000"
#ETCD_QUOTA_BACKEND_BYTES="0"
#ETCD_MAX_REQUEST_BYTES="1572864"
#ETCD_GRPC_KEEPALIVE_MIN_TIME="5s"
#ETCD_GRPC_KEEPALIVE_INTERVAL="2h0m0s"
#ETCD_GRPC_KEEPALIVE_TIMEOUT="20s"
#
#[Clustering]
#更改为本机IP
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://192.168.0.230:2380" 
#更改为本机IP
ETCD_ADVERTISE_CLIENT_URLS="https://192.168.0.230:2379"  
#ETCD_DISCOVERY=""
#ETCD_DISCOVERY_FALLBACK="proxy"
#ETCD_DISCOVERY_PROXY=""
#ETCD_DISCOVERY_SRV=""
#etcd集群的3个IP
ETCD_INITIAL_CLUSTER="etcd01=https://192.168.0.230:2380,etcd02=https://192.168.0.231:2380,etcd03=https://192.168.0.232:2380"
ETCD_INITIAL_CLUSTER_TOKEN="etcd-cluster"
ETCD_INITIAL_CLUSTER_STATE="new"
#ETCD_STRICT_RECONFIG_CHECK="true"
#ETCD_ENABLE_V2="true"
#
#[Proxy]
#ETCD_PROXY="off"
#ETCD_PROXY_FAILURE_WAIT="5000"
#ETCD_PROXY_REFRESH_INTERVAL="30000"
#ETCD_PROXY_DIAL_TIMEOUT="1000"
#ETCD_PROXY_WRITE_TIMEOUT="5000"
#ETCD_PROXY_READ_TIMEOUT="0"
#
#[Security]
#刚生成的证书        
ETCD_CERT_FILE="/etc/etcd/ssl/etcd.pem"
ETCD_KEY_FILE="/etc/etcd/ssl/etcd-key.pem"
ETCD_CLIENT_CERT_AUTH="true"
ETCD_TRUSTED_CA_FILE="/etc/etcd/ssl/ca.pem"
ETCD_AUTO_TLS="true"
ETCD_PEER_CERT_FILE="/etc/etcd/ssl/etcd.pem"
ETCD_PEER_KEY_FILE="/etc/etcd/ssl/etcd-key.pem"
ETCD_PEER_CLIENT_CERT_AUTH="true"
ETCD_PEER_TRUSTED_CA_FILE="/etc/etcd/ssl/ca.pem"
ETCD_PEER_AUTO_TLS="true"
#
#[Logging]
#ETCD_DEBUG="false"
#ETCD_LOG_PACKAGE_LEVELS=""
#ETCD_LOG_OUTPUT="default"
#
#[Unsafe]
#ETCD_FORCE_NEW_CLUSTER="false"
#
#[Version]
#ETCD_VERSION="false"
#ETCD_AUTO_COMPACTION_RETENTION="0"
#
#[Profiling]
#ETCD_ENABLE_PPROF="false"
#ETCD_METRICS="basic"
#
#[Auth]
#ETCD_AUTH_TOKEN="simple"
```

上面注释需的地方需要根据环境更改，注释影响启动的话，直接删除，还需要的操作，并启动etcd服务

```
chmod 644 /etc/etcd/ssl/*
 
systemctl daemon-reload
systemctl enable etcd
systemctl start etcd
export ETCDCTL_API=3
```

**启动etcd的时候卡住**？ 如果是etcd集群，只启动一个etcd服务的话会这样，当启动第二个etcd服务的时候，第一个etcd马上就启动好

查看etcd服务状态

```
# etcdctl --cacert=/etc/etcd/ssl/ca.pem --cert=/etc/etcd/ssl/etcd.pem --key=/etc/etcd/ssl/etcd-key.pem --endpoints=https://192.168.0.230:2379,https://192.168.0.231:2379,https://192.168.0.232:2379 endpoint health
https://192.168.0.230:2379 is healthy: successfully committed proposal: took = 2.249354ms
https://192.168.0.231:2379 is healthy: successfully committed proposal: took = 2.19648ms
https://192.168.0.232:2379 is healthy: successfully committed proposal: took = 1.64258ms
 
# etcdctl member list
# curl -k --key /etc/etcd/ssl/etcd-key.pem --cert /etc/etcd/ssl/etcd.pem https://192.168.0.230:2380/members
 
# etcdctl endpoint health
127.0.0.1:2379 is healthy: successfully committed proposal: took = 1.926097ms
```

如果重置了kubernetes集群，即kubeadm reset，需要停止etcd服务，并删除/var/lib/etcd/目录下文件，以免影响新创建的k8s集群

tips:  etcd主机如果有一台意外关机，另外2台状态正常

出意外的主机启动etcd服务提示

```
etcd: member 1ce6d6d01109192 has already been bootstrapped
systemd: etcd.service: main process exited, code=exited, status=1/FAILURE
```

移除/var/lib/etcd文件夹

```
etcd: restarting member 1ce6d6d01109192 in cluster 194cd14a
48430083 at commit index 6799841
etcd: 1ce6d6d01109192 state.commit 6799841 is out of range 
[6800068, 6800068]
bash: panic: 1ce6d6d01109192 state.commit 6799841 is out of range [6800068, 6800068]
```

解决方式，编辑etcd配置文件后，再次启动

```
ETCD_INITIAL_CLUSTER_STATE="existing"
#ETCD_INITIAL_CLUSTER_STATE="new"
```

由于etcdctl_api错误的问题：

```
# etcdctl member list
client: etcd cluster is unavailable or misconfigured; error #0: x509: certificate signed by unknown authority
; error #1: x509: certificate signed by unknown authority
; error #2: dial tcp 192.168.1.1:2379: getsockopt: connection refused
 
# export ETCDCTL_API=3
# etcdctl member list
```

### 安装docker服务

```
# yum install yum-utils -y
# yum-config-manager  --add-repo  https://download.docker.com/linux/centos/docker-ce.repo
# yum install docker-ce -y
# cat << EOF >> /etc/docker/daemon.json 
{
  "bip": "172.18.1.1/24",
  "fixed-cidr": "172.18.1.0/24",
  "exec-opts": ["native.cgroupdriver=systemd"]
}
EOF
 
systemctl enable docker && systemctl start docker
```

docker的ip改不改无所谓，不过cgroupdriver需要k8s master和 node节点统一

如果用度娘网盘的压缩包，直接 yum localinstall -y *.rpm

node节点的docker配置

```
# cat /etc/docker/daemon.json 
{
  "exec-opts": ["native.cgroupdriver=systemd"]
}
```

kubernetes集群和node节点cgroupdriver都使用systemd

### kubernetes master节点操作

安装rpm包

```
# ls k8s/rpm
kubeadm-1.9.4-0.x86_64.rpm  kubelet-1.9.4-0.x86_64.rpm
kubectl-1.9.4-0.x86_64.rpm  kubernetes-cni-0.6.0-0.x86_64.rpm
 
# yum localinstall -y *.rpm
# mkdir /etc/kubernetes/pki     #晚些时候scp node1节点配置到另外2个节点的这个目录
```

导入images

```
# ls k8s/images/
coredns.tar           k8s-dns-sidecar.tar         kube-proxy.tar             pause.tar
k8s-dns-dnsmasq.tar   kube-apiserver-v1.9.4.tar   kube-router.tar
k8s-dns-kube-dns.tar  kube-controller-v1.9.4.tar  kube-scheduler-v1.9.4.tar
 
# for i in `ls .`;do docker load < $i;done
```

kubernetes & etcd 用同样的证书

```
mkdir -p /etc/kubernetes/pki
mkdir /etc/kubernetes/ssl
cp /etc/etcd/ssl/etcd.pem /etc/kubernetes/ssl/
cp /etc/etcd/ssl/etcd-key.pem /etc/kubernetes/ssl/
cp /etc/etcd/ssl/ca.pem /etc/kubernetes/ssl/
```

配置kubernetes master节点

```
# cat /etc/kubernetes/config.yaml 
apiVersion: kubeadm.k8s.io/v1alpha1
kind: MasterConfiguration
etcd:
  endpoints:
  - https://192.168.0.230:2379    #3个master节点
  - https://192.168.0.231:2379
  - https://192.168.0.232:2379
  caFile: /etc/etcd/ssl/ca.pem  #和etcd使用一样的证书
  certFile: /etc/etcd/ssl/etcd.pem 
  keyFile: /etc/etcd/ssl/etcd-key.pem
  dataDir: /var/lib/etcd
networking:
  podSubnet: 10.244.0.0/16
kubernetesVersion: 1.9.4
api:
  advertiseAddress: "192.168.0.238"   #api的地址，即keepalived的VIP
token: "4bdbca.6e3531d0ec698d96"
tokenTTL: "0s"
apiServerCertSANs:
- etcd01
- etcd02
- etcd03
- 192.168.0.230
- 192.168.0.231
- 192.168.0.232
- 192.168.0.238
- 127.0.0.1
- kubernetes
- kubernetes.default
- kubernetes.default.svc
- kubernetes.default.svc.cluster
- kubernetes.default.svc.cluster.local
- 10.96.0.1
- 10.244.0.1
featureGates:
  CoreDNS: true
```

token生成:

```
kubeadm token generate
```

关于ip地址段，docker的ip默认统一为 172.17.0.1，上面安装docker的时候修改为了172.18.1.1，其实修不修改无所谓。IP地址段主要一个是node主机节点的IP，一个是pod的IP

node主机ip范围，每一个节点（master和node）必须有一个24位掩码的网段，比如 10.244.0.1/24、 10.244.1.1/24，网卡为 kube-bridge，所以下面用21位的子网掩码，集群最多可以是8台（包括master和node）

```
/etc/kubernetes/config.yaml
networking: podSubnet: 10.244.0.0/21
```

kubernetes pod IP范围(不能和docker或物理网络子网冲突)：

```
/etc/kubernetes/manifests/kube-apiserver.yaml
    --service-cluster-ip-range=10.96.0.0/12
```

默认是10.96.0.0/12，即pod的ip数量最大为 1048574，第一个可用ip ： 10.96.0.1

最后一个可用ip ：10.111.255.254

初始化kubeadm

```
# kubeadm init --config /etc/kubernetes/config.yaml 
[init] Using Kubernetes version: v1.9.4
[init] Using Authorization modes: [Node RBAC]
[preflight] Running pre-flight checks.
	[WARNING Firewalld]: firewalld is active, please ensure ports [6443 10250] are open or your cluster may not function correctly
	[WARNING FileExisting-crictl]: crictl not found in system path
[preflight] Starting the kubelet service
[certificates] Generated ca certificate and key.
[certificates] Generated apiserver certificate and key.
[certificates] apiserver serving cert is signed for DNS names [k8smaster01 kubernetes kubernetes.default kubernetes.default.svc kubernetes.default.svc.cluster.local etcd01 etcd02 etcd03] and IPs [10.96.0.1 192.168.0.238 192.168.0.230 192.168.0.231 192.168.0.232 192.168.0.238]
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
[init] Waiting for the kubelet to boot up the control plane as Static Pods from directory "/etc/kubernetes/manifests".
[init] This might take a minute or longer if the control plane images have to be pulled.
[apiclient] All control plane components are healthy after 32.502523 seconds
[uploadconfig] Storing the configuration used in ConfigMap "kubeadm-config" in the "kube-system" Namespace
[markmaster] Will mark node k8smaster01 as master by adding a label and a taint
[markmaster] Master k8smaster01 tainted and labelled with key/value: node-role.kubernetes.io/master=""
[bootstraptoken] Using token: 4bdbca.6e3531d0ec698d96
[bootstraptoken] Configured RBAC rules to allow Node Bootstrap tokens to post CSRs in order for nodes to get long term certificate credentials
[bootstraptoken] Configured RBAC rules to allow the csrapprover controller automatically approve CSRs from a Node Bootstrap Token
[bootstraptoken] Configured RBAC rules to allow certificate rotation for all node client certificates in the cluster
[bootstraptoken] Creating the "cluster-info" ConfigMap in the "kube-public" namespace
[addons] Applied essential addon: kube-dns
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
 
  kubeadm join --token 4bdbca.6e3531d0ec698d96 192.168.0.238:6443 --discovery-token-ca-cert-hash sha256:1a2e99b078954fd94fe93dcf9f968f7d8d6a3cb5e6473e262ed7d33b3fe40c51
```

有问题查看/var/log/message

查看kubernetes服务状态

```
# export KUBECONFIG=/etc/kubernetes/admin.conf
 
[root@k8smaster01 ~]# kubectl get cs
NAME                 STATUS    MESSAGE              ERROR
scheduler            Healthy   ok                   
controller-manager   Healthy   ok                   
etcd-0               Healthy   {"health": "true"}   
etcd-1               Healthy   {"health": "true"}   
etcd-2               Healthy   {"health": "true"}   
[root@k8smaster01 ~]# kubectl get nodes
NAME          STATUS     ROLES     AGE       VERSION
k8smaster01   NotReady   master    23s       v1.9.4
[root@k8smaster01 ~]# kubectl get po -n kube-system
NAME                                  READY     STATUS    RESTARTS   AGE
coredns-65dcdb4cf-r2lrk               0/1       Pending   0          1m
kube-apiserver-k8smaster01            1/1       Running   0          51s
kube-controller-manager-k8smaster01   1/1       Running   0          1m
kube-proxy-r9l5v                      1/1       Running   0          1m
kube-scheduler-k8smaster01            1/1       Running   0          58s
```

```
# kubectl config view
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: REDACTED
    server: https://192.168.0.238:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes
current-context: kubernetes-admin@kubernetes
kind: Config
preferences: {}
users:
- name: kubernetes-admin
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED
```

### 配置kube-rouer

```
wget https://raw.githubusercontent.com/cloudnativelabs/kube-router/master/daemonset/kubeadm-kuberouter-all-features.yaml
 
# kubectl create -f kubeadm-kuberouter-all-features.yaml 
configmap "kube-router-cfg" created
daemonset "kube-router" created
serviceaccount "kube-router" created
clusterrole "kube-router" created
clusterrolebinding "kube-router" created
```

```
[root@k8smaster01 ~]# kubectl get po -n kube-system
NAME                                  READY     STATUS    RESTARTS   AGE
coredns-65dcdb4cf-r2lrk               1/1       Running   0          3m
kube-apiserver-k8smaster01            1/1       Running   0          2m
kube-controller-manager-k8smaster01   1/1       Running   0          3m
kube-proxy-r9l5v                      1/1       Running   0          3m
kube-router-tpjls                     1/1       Running   0          1m
kube-scheduler-k8smaster01            1/1       Running   0          3m
```

删除kube-proxy,现在因为kube-router也提供服务代理。运行以下命令来删除kube-proxy并清除它可能已经完成的任何iptables配置

```
kubectl -n kube-system delete ds kube-proxy
docker run --privileged --net=host gcr.io/google_containers/kube-proxy-amd64:v1.9.4 kube-proxy --cleanup-iptables
 
# 如果遇到了这个错误，可以忽略
docker run --privileged --net=host gcr.io/google_containers/kube-proxy-amd64:v1.9.4 kube-proxy --cleanup-iptables
Flag --cleanup-iptables has been deprecated, This flag is replaced by --cleanup.
W0806 01:42:32.190641       1 server.go:185] WARNING: all flags other than --config, --write-config-to, and --cleanup are deprecated. Please begin using a config file ASAP.
time="2018-08-06T01:42:32Z" level=warning msg="Running modprobe ip_vs failed with message: `modprobe: ERROR: ../libkmod/libkmod.c:586 kmod_search_moddep() could not open moddep file '/lib/modules/3.10.0-693.el7.x86_64/modules.dep.bin'\nmodprobe: WARNING: Module ip_vs not found in directory /lib/modules/3.10.0-693.el7.x86_64`, error: exit status 1"
I0806 01:42:32.194302       1 server.go:426] Version: v1.9.4
E0806 01:42:32.209299       1 proxier.go:610] Failed to execute iptables-restore for filter: exit status 1 (iptables-restore: line 5 failed
)
error: encountered an error while tearing down rules.
```

```
# kubectl get po -n kube-system
NAME                                  READY     STATUS    RESTARTS   AGE
coredns-65dcdb4cf-kwqmz               1/1       Running   0          10m
kube-apiserver-k8smaster01            1/1       Running   0          10m
kube-controller-manager-k8smaster01   1/1       Running   0          9m
kube-router-h8hbm                     1/1       Running   0          5m
kube-scheduler-k8smaster01            1/1       Running   0          9m
```

### 扩展其他主节点

```
证书scp一次就可以
# scp -r /etc/kubernetes/ssl/* k8smaster02:/etc/kubernetes/ssl
# scp -r /etc/kubernetes/ssl/* k8smaster03:/etc/kubernetes/ssl
 
kubernetes配置文件在master1 每次初始化后都需要更新
# scp /etc/kubernetes/pki/* k8smaster02:/etc/kubernetes/pki/
# scp /etc/kubernetes/config.yaml k8smaster02:/etc/kubernetes/
# scp /etc/kubernetes/pki/* k8smaster03:/etc/kubernetes/pki/
# scp /etc/kubernetes/config.yaml k8smaster03:/etc/kubernetes/
```

k8smaster02和k8smaster03节点一样执行初始化kubeadm

```
[root@k8smaster01 ~]# kubectl get nodes
NAME          STATUS    ROLES     AGE       VERSION
k8smaster01   Ready     master    8m        v1.9.4
k8smaster02   Ready     master    1m        v1.9.4
k8smaster03   Ready     master    17s       v1.9.4
```

master2和master3都加入集群后，确保kube-proxy被删除

```
kubectl -n kube-system delete ds kube-proxy
kubectl get po -n kube-system
```

### 配置kubernetes node节点

```
# tree node
node
├── docker
│   ├── docker-ce-17.03.2.ce-1.el7.centos.x86_64.rpm
│   └── docker-ce-selinux-17.03.2.ce-1.el7.centos.noarch.rpm
├── images
│   ├── kube-proxy.tar
│   ├── kube-router.tar
│   └── pause.tar
└── rpm
    ├── kubeadm-1.9.4-0.x86_64.rpm
    ├── kubectl-1.9.4-0.x86_64.rpm
    ├── kubelet-1.9.4-0.x86_64.rpm
    └── kubernetes-cni-0.6.0-0.x86_64.rpm
```

node节点安装docker，kubeadm、kubectl、kubelet、kubernetes-cni后，导入kube-proxy、kube-router、pause 3个images

执行kubeadm join即可，在master节点查看k8s服务状态

```
[root@k8smaster01 ~]# kubectl get po -n kube-system
NAME                                  READY     STATUS    RESTARTS   AGE
coredns-65dcdb4cf-r2lrk               1/1       Running   0          1h
kube-apiserver-k8smaster01            1/1       Running   0          1h
kube-apiserver-k8smaster02            1/1       Running   0          1h
kube-apiserver-k8smaster03            1/1       Running   0          1h
kube-controller-manager-k8smaster01   1/1       Running   0          1h
kube-controller-manager-k8smaster02   1/1       Running   0          1h
kube-controller-manager-k8smaster03   1/1       Running   0          1h
kube-router-chcfz                     1/1       Running   0          1h
kube-router-l7sr6                     1/1       Running   0          1h
kube-router-tpjls                     1/1       Running   0          1h
kube-router-zdmkt                     1/1       Running   0          1h
kube-scheduler-k8smaster01            1/1       Running   0          1h
kube-scheduler-k8smaster02            1/1       Running   0          1h
kube-scheduler-k8smaster03            1/1       Running   0          1h
```

这时候coredns是单节点的，需要扩展为3个节点

```
# kubectl scale --replicas=3 deployment/coredns -n kube-system
deployment "coredns" scaled
```

### k8s1.9版本的dashboard界面

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/master/src/deploy/alternative/kubernetes-dashboard.yaml
```

```
# vim dashboard-rbac.yaml
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

再安装完traefik后，随机关闭一台master节点，测试服务可用性，证明服务可以不间断访问

```
# kubectl get po -n kube-system -o wide
NAME                                    READY     STATUS    RESTARTS   AGE       IP              NODE
coredns-65dcdb4cf-6qpcz                 1/1       Running   0          17h       10.244.5.35     k8snode03
coredns-65dcdb4cf-889cv                 1/1       Running   1          18h       10.244.2.3      k8smaster03
coredns-65dcdb4cf-gpgfr                 1/1       Running   0          17h       10.244.3.93     k8snode01
kube-apiserver-k8smaster01              1/1       Running   4          17h       192.168.0.230   k8smaster01
kube-apiserver-k8smaster02              1/1       Running   1          17h       192.168.0.231   k8smaster02
kube-apiserver-k8smaster03              1/1       Running   1          18h       192.168.0.232   k8smaster03
kube-controller-manager-k8smaster01     1/1       Running   4          17h       192.168.0.230   k8smaster01
kube-controller-manager-k8smaster02     1/1       Running   2          17h       192.168.0.231   k8smaster02
kube-controller-manager-k8smaster03     1/1       Running   4          18h       192.168.0.232   k8smaster03
kube-router-h8hbm                       1/1       Running   4          18h       192.168.0.230   k8smaster01
kube-router-kf94k                       1/1       Running   0          18h       192.168.0.235   k8snode03
kube-router-l4r5l                       1/1       Running   0          18h       192.168.0.233   k8snode01
kube-router-l7hqr                       1/1       Running   1          18h       192.168.0.232   k8smaster03
kube-router-q9bpx                       1/1       Running   0          18h       192.168.0.234   k8snode02
kube-router-qsktr                       1/1       Running   5          18h       192.168.0.231   k8smaster02
kube-scheduler-k8smaster01              1/1       Running   4          17h       192.168.0.230   k8smaster01
kube-scheduler-k8smaster02              1/1       Running   1          17h       192.168.0.231   k8smaster02
kube-scheduler-k8smaster03              1/1       Running   5          18h       192.168.0.232   k8smaster03
kubernetes-dashboard-7bc6584fc6-77w5x   1/1       Running   0          17h       10.244.5.34     k8snode03
kubernetes-dashboard-7bc6584fc6-m8mpf   1/1       Running   0          18h       10.244.3.92     k8snode01
kubernetes-dashboard-7bc6584fc6-wwlxl   1/1       Running   0          17h       10.244.4.32     k8snode02
traefik-ingress-controller-5hrc7        1/1       Running   0          17h       192.168.0.233   k8snode01
traefik-ingress-controller-fqnvv        1/1       Running   0          17h       192.168.0.234   k8snode02
traefik-ingress-controller-k2nkx        1/1       Running   0          17h       192.168.0.235   k8snode03
```

```
# kubectl get svc -n kube-system|grep dashboard
kubernetes-dashboard      NodePort    10.110.70.105    <none>        8001:32655/TCP                18h
```

这时候在浏览器访问3个node ip中某一个都可以，加上nodeport暴露的端口，NODE_IP:32655即可打开kubernetes-dashboard界面

### DNS使用默认的kube-dns

(kubedns/dnsmasq/sidecar)

kubedns监控master节点服务和终结点的变化，dnsmasq就是一个轻量级dns服务器

重置kubernetes集群

```
kubeadm reset
systemctl stop etcd
rm -rf /var/lib/etcd/member
```

修改kubernetes配置，取消coredns

```
/etc/kubernetes/config.yaml
#featureGates:
#  CoreDNS: true
```

进行初始化

```
kubeadm init --config /etc/kubernetes/config.yaml
```

查看状态，需要node节点

```
[root@k8smaster01 ~]# kubectl get nodes
NAME          STATUS     ROLES     AGE       VERSION
k8smaster01   Ready      master    17m       v1.9.4
k8smaster02   Ready      master    12m       v1.9.4
k8smaster03   Ready      master    8m        v1.9.4
[root@k8smaster01 ~]# kubectl get cs
NAME                 STATUS    MESSAGE              ERROR
controller-manager   Healthy   ok                   
scheduler            Healthy   ok                   
etcd-0               Healthy   {"health": "true"}   
etcd-2               Healthy   {"health": "true"}   
etcd-1               Healthy   {"health": "true"}   
[root@k8smaster01 ~]# kubectl get po -n kube-system
NAME                                  READY     STATUS    RESTARTS   AGE
kube-apiserver-k8smaster01            1/1       Running   0          15m
kube-apiserver-k8smaster02            1/1       Running   0          20m
kube-apiserver-k8smaster03            1/1       Running   0          16m
kube-controller-manager-k8smaster01   1/1       Running   0          15m
kube-controller-manager-k8smaster02   1/1       Running   0          20m
kube-controller-manager-k8smaster03   1/1       Running   0          16m
kube-dns-6f4fd4bdf-tb5bh              3/3       Running   0          25m
kube-proxy-8xswz                      1/1       Running   0          20m
kube-proxy-c9tvp                      1/1       Running   0          16m
kube-proxy-m2jr2                      1/1       Running   0          25m
kube-scheduler-k8smaster01            1/1       Running   0          15m
kube-scheduler-k8smaster02            1/1       Running   0          20m
kube-scheduler-k8smaster03            1/1       Running   0          16m
```

kubernetes 1.9 calico插件

```
wget https://docs.projectcalico.org/v3.0/getting-started/kubernetes/installation/hosted/kubeadm/1.7/calico.yaml
```

calico插件离线tar包链接：https://pan.baidu.com/s/1XFY6O5GMPj7X5nzZgB_iHA 密码：985d

![kubernetes1.9版本集群配置向导 - 第1张](../images/2018/03/%E5%BE%AE%E4%BF%A1%E6%88%AA%E5%9B%BE_20180727094123.png)

### 遇到的错误

```
docker-ce-17.03.2.ce-1.el7.centos.x86_64 from /docker-ce-17.03.2.ce-1.el7.centos.x86_64
docker-ce-selinux-17.03.2.ce-1.el7.centos.noarch from /docker-ce-selinux-17.03.2.ce-1.el7.centos.noarch
# yum erase docker-engine-selinux
```

```
Container runtime network not ready: NetworkReady=false reason:NetworkPluginNotReady message:docker: network plugin is not ready: cni config uninitialized
Unable to update cni config: No networks found in /etc/cni/net.d
 
/etc/systemd/system/kubelet.service.d/10-kubeadm.conf
Environment="KUBELET_NETWORK_ARGS="
systemctl daemon-reload
```

```
Unable to connect to the server: x509: certificate signed by unknown authority (possibly because of "crypto/rsa: verification error" while trying to verify candidate authority certificate "kubernetes")
需要重新生成证书
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
scp /etc/kubernetes/pki/* k8smaster02:/etc/kubernetes/pki/
export KUBECONFIG=/etc/kubernetes/admin.conf
```

```
github.com/coredns/coredns/plugin/kubernetes/controller.go:259: Failed to list *v1.Endpoints: Get https://10.96.0.1:443/api/v1/endpoints?resourceVersion=0: dial tcp 10.96.0.1:443: getsockopt: connection timed out
 
Kubedns 1.14.7 does not work well with kubernetes 1.9.1. In my case, kubedns was trying to connect to apiserver using 443 and not, as configured, 6443.
 
When I changed the image version to 1.14.8 (newest - kubedns github), kubedns recognized the apiserver port properly. No problems any more:
 
kubectl edit deploy kube-dns  -n kube-system
#change to the image version to  1.14.8  and works
 
If the issue is still seen, also do:
 
kubectl create configmap --namespace=kube-system kube-dns
kubectl delete pod <name of kube-dns pod> --namespace=kube-system
# kube-dns should restart and work now
```

```
level=error msg="[graphdriver] prior storage driver overlay2 failed: driver not supported"
dockerd: Error starting daemon: error initializing graphdriver: driver not supported
# cat /etc/docker/daemon.json 
{
  "exec-opts": ["native.cgroupdriver=systemd"]
}
```

```
如果开启firewall
master:
firewall-cmd --permanent --add-rich-rule="rule family="ipv4" source address="192.168.0.0/23" port protocol="tcp" port="6443-10255" accept"
firewall-cmd --permanent --add-rich-rule="rule family="ipv4" source address="192.168.0.0/23" port protocol="tcp" port="2379-2380" accept"
firewall-cmd --permanent --add-rich-rule="rule family="ipv4" source address="192.168.0.0/23" port protocol="tcp" port="80-443" accept"
 
node:
firewall-cmd --permanent --add-rich-rule="rule family="ipv4" source address="192.168.0.0/23" port protocol="tcp" port="10250-10255" accept"
firewall-cmd --permanent --add-rich-rule="rule family="ipv4" source address="192.168.0.0/23" port protocol="tcp" port="30000-32767" accept"
 
iptables -P FORWARD ACCEPT
```

```
保存配置
kubectl get configmap kube-proxy  -n kube-system -o yaml > kube-proxy.yaml
kubectl get deployment kube-dns -n kube-system -o yaml > kube-dns.yaml
```

```
Apr  3 18:39:59 localhost kubelet: E0403 18:39:59.502903    3999 reflector.go:205] k8s.io/kubernetes/pkg/kubelet/kubelet.go:470: Failed to list *v1.Service: Get https://192.168.0.238:6443/api/v1/services?limit=500&resourceVersion=0: dial tcp 192.168.0.238:6443: connect: no route to host
Apr  3 18:39:59 localhost kubelet: E0403 18:39:59.503962    3999 reflector.go:205] k8s.io/kubernetes/pkg/kubelet/kubelet.go:479: Failed to list *v1.Node: Get https://192.168.0.238:6443/api/v1/nodes?fieldSelector=metadata.name%3Dk8snode02&limit=500&resourceVersion=0: dial tcp 192.168.0.238:6443: connect: no route to host
Apr  3 18:40:00 localhost kubelet: E0403 18:40:00.502486    3999 reflector.go:205] k8s.io/kubernetes/pkg/kubelet/config/apiserver.go:47: Failed to list *v1.Pod: Get https://192.168.0.238:6443/api/v1/pods?fieldSelector=spec.nodeName%3Dk8snode02&limit=500&resourceVersion=0: dial tcp 192.168.0.238:6443: connect: no route to host
 
原因是coredns和kube-proxy冲突了，所以需要删除kube-proxy
kubectl -n kube-system delete ds kube-proxy
```

```
docker run --privileged --net=host gcr.io/google_containers/kube-proxy-amd64:v1.9.4 kube-proxy --cleanup-iptables
Flag --cleanup-iptables has been deprecated, This flag is replaced by --cleanup.
W0806 01:42:32.190641       1 server.go:185] WARNING: all flags other than --config, --write-config-to, and --cleanup are deprecated. Please begin using a config file ASAP.
time="2018-08-06T01:42:32Z" level=warning msg="Running modprobe ip_vs failed with message: `modprobe: ERROR: ../libkmod/libkmod.c:586 kmod_search_moddep() could not open moddep file '/lib/modules/3.10.0-693.el7.x86_64/modules.dep.bin'\nmodprobe: WARNING: Module ip_vs not found in directory /lib/modules/3.10.0-693.el7.x86_64`, error: exit status 1"
I0806 01:42:32.194302       1 server.go:426] Version: v1.9.4
E0806 01:42:32.209299       1 proxier.go:610] Failed to execute iptables-restore for filter: exit status 1 (iptables-restore: line 5 failed
)
error: encountered an error while tearing down rules.
 
提示是 ip_vs 模块没有加载，不过 modprobe ip_vs ,lsmod 都有此模块，官方文档说更改一行代码，再重新编译kubernetes 二进制文件可以解决，不过忽略这个错误也可以
# modprobe ip_vs
# lsmod |grep ip_vs
ip_vs_rr               12600  4 
ip_vs                 141092  7 ip_vs_rr,xt_ipvs
nf_conntrack          133387  7 ip_vs,nf_nat,nf_nat_ipv4,xt_conntrack,nf_nat_masquerade_ipv4,nf_conntrack_netlink,nf_conntrack_ipv4
libcrc32c              12644  4 xfs,ip_vs,nf_nat,nf_conntrack
```

参考文档

<http://www.toxingwang.com/cloud/3127.html>

<https://k8smeetup.github.io/docs/setup/independent/high-availability/>

<https://www.kubernetes.org.cn/3536.html>

<https://mritd.me/2017/10/09/set-up-kubernetes-1.8-ha-cluster/>

<https://kubernetes.io/docs/setup/independent/high-availability/>

<https://docs.nginx.com/nginx/admin-guide/high-availability/ha-keepalived-nodes/>

<https://github.com/bbotte/kube-router/blob/master/Documentation/kubeadm.md>

<http://blog.51cto.com/net592/2059315>



2018年03月16日 于 [linux工匠](http://www.bbotte.com/) 发表