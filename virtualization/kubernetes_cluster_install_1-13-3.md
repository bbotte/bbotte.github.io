---
layout: default
---

## kubernetes集群安装步骤(Version:1.13.3)

###### 备注：centos 7.5 最小化安装

##### 系统设置

| 功能                     | VIP              | 端口映射      |
| ---------------------- | ---------------- | --------- |
| kube-Api端口，用于dashboard | 192.168.0.120/32 | 6443:6443 |
| Node高可用端口，用于web访问      | 192.168.0.130/32 | 8112:80   |
| mysql MHA              | 192.168.0.140/32 | 3306:3306 |

设置主机名称(IP和主机名根据实际情况改动)

```
hostnamectl --static set-hostname k8sm1
exec $SHELL
cat <<EOF >> /etc/hosts
192.168.0.121 k8sm1
192.168.0.122  k8sm2
192.168.0.123  k8sm3
192.168.0.124  k8sn1
192.168.0.131  SLB1
192.168.0.132  SLB2
192.168.0.150  GFS01
192.168.0.151  GFS02
192.168.0.152  DBx01
192.168.0.153  DBx02
192.168.0.154  MON01
EOF
```

更改分区(可选)

```
df -Th
umount /home
lvreduce -L 10G /dev/mapper/centos-home
mkfs.xfs /dev/mapper/centos-home -f
mount -a
lvextend -l +100%FREE /dev/mapper/centos-root
xfs_growfs /dev/mapper/centos-root
df -Th
```

以下通用

```
swapoff -a
sed -i 's/.*swap.*/#&/' /etc/fstab
systemctl stop firewalld
systemctl disable firewalld
sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config 
setenforce 0
iptables -P FORWARD ACCEPT
yum install -y epel-release vim vim-enhanced wget lrzsz unzip ntpdate sysstat dstat wget mlocate mtr lsof iotop bind-utils git net-tools ipvsadm ipset
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
cat <<EOF >> /etc/sysctl.conf
net.ipv4.ip_forward=1
fs.file-max = 655350
net.ipv4.tcp_max_syn_backlog = 65536
net.core.netdev_max_backlog =  32768
net.core.somaxconn = 32768
net.core.wmem_default = 8388608
net.core.rmem_default = 8388608
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_timestamps = 0
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 2
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_mem = 94500000 915000000 927000000
net.ipv4.tcp_max_orphans = 3276800
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 600
net.ipv4.ip_local_port_range = 1024  65535
net.netfilter.nf_conntrack_tcp_timeout_close_wait = 60
net.netfilter.nf_conntrack_tcp_timeout_fin_wait = 120
net.nf_conntrack_max=655360
net.netfilter.nf_conntrack_max=655360
net.netfilter.nf_conntrack_tcp_timeout_established=180
net.netfilter.nf_conntrack_tcp_timeout_time_wait=30
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
```

3台master主机执行：

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
sysctl -p /etc/sysctl.conf
/sbin/sysctl -p
```

配置DNS服务(可选)

如果数据库在kubernetes集群外部，需要配置DNS服务，比如在2台gfs主机或lb主机上安装dnsmasq

```
yum install dnsmasq -y
sed -i '111 alisten-address=10.11.11.10' /etc/dnsmasq.conf
cat > /etc/dnsmasq.d/dns.conf <<EOF
address=/db-com/192.168.0.140
EOF
cat >> /etc/sysconfig/network-scripts/ifcfg-eth0 <<EOF
DNS1="223.5.5.5"
DNS2="8.8.8.8"
EOF
systemctl enable dnsmasq && systemctl start dnsmasq
```

k8s master节点和node节点都使用此dns

```
cat > /etc/resolv.conf <<EOF
> nameserver 10.11.11.10
> nameserver 10.11.11.11
> EOF
cat >> /etc/sysconfig/network-scripts/ifcfg-eth0 <<EOF
DNS1="10.11.11.10"
DNS2="10.11.11.11"
EOF
```



#### 设置kube_api_VIP(IP和主机名根据实际情况改动)

3台master主机安装

```
yum install keepalived ipvsadm -y
mv /etc/keepalived/keepalived.conf{,.def}
cat >> /etc/keepalived/keepalived.conf <<EOF
! Configuration File for keepalived
global_defs {
   notification_email {
      bbotte@163.com
   }
   router_id LVS_k8sm1    #change me
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
    virtual_router_id 99    #虚拟路由id
    priority 100            #权重,配置不同数值，另2台为99,98
    advert_int 3
    # 本机ip
    mcast_src_ip 192.168.0.121
    authentication {
        auth_type PASS
        auth_pass bbotte_k8smaster
    }
    unicast_peer {
        #对方的ip
        192.168.0.122
        192.168.0.123
    }
    virtual_ipaddress {
        192.168.0.120/24
    }
    track_script {
        CheckK8sMaster    
    }
}
EOF
systemctl enable keepalived && systemctl restart keepalived
ipvsadm -Ln
sleep 10
ip a
```

#### 生成证书(仅需其中一台，在master1操作)

k8s_1.13.3.tar.gz度娘网盘: https://pan.baidu.com/s/1OsIQErnhPMkWvY7VM_BQjA 提取码: ifiu 
cfssl证书生成: https://pan.baidu.com/s/1SYhpI81ONNvwA75HFQrDUQ 提取码: vuxc，下面生成证书使用，下载这个只有5M


```
tar -xf k8s_1.13.3.tar.gz
cp k8s/ssl/cfssl* /usr/bin/
mkdir k8s/ssl/conf
cat > k8s/ssl/conf/etcd-csr.json <<EOF
{
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "O": "etcd",
      "OU": "etcd Security",
      "L": "Shanghai",
      "ST": "Shanghai",
      "C": "CN"
    }
  ],
  "CN": "etcd",
  "hosts": [
    "127.0.0.1",
    "192.168.0.121",
    "192.168.0.122",
    "192.168.0.123",
    "192.168.0.120"
  ]
}
EOF
cat > k8s/ssl/conf/etcd-gencert.json <<EOF
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
EOF
cat > k8s/ssl/conf/etcd-root-ca-csr.json <<EOF
{
  "key": {
    "algo": "rsa",
    "size": 4096
  },
  "names": [
    {
      "O": "etcd",
      "OU": "etcd Security",
      "L": "Shanghai",
      "ST": "Shanghai",
      "C": "CN"
    }
  ],
  "ca": {
    "expiry": "87600h"
  }
}
EOF
cd k8s/ssl/conf/
cfssl gencert --initca=true etcd-root-ca-csr.json | cfssljson --bare ca
cfssl gencert --ca ca.pem --ca-key ca-key.pem --config etcd-gencert.json etcd-csr.json | cfssljson --bare etcd
```

```
for i in k8sm1 k8sm2 k8sm3 ;do ssh ${i} mkdir -p /etc/etcd/ssl; scp etcd-key.pem etcd.pem ca.pem ${i}:/etc/etcd/ssl;done
cd
```

#### etcd集群创建(IP和主机名根据实际情况改动)

务必安装etcd 3.3.13以上版本，避免 etcd read-only range request took too long

```
cd k8s/etcd
tar -xf etcd-v3.3.13-linux-amd64.tar.gz
cp etcd.conf /etc/etcd/
# change etcd.conf configure
cp etcd.service /usr/lib/systemd/system/etcd.service
cp etcd-v3.3.13-linux-amd64/etcd /usr/bin/
cp etcd-v3.3.13-linux-amd64/etcdctl /usr/bin/
rm -rf etcd-v3.3.13-linux-amd64
chmod +x /usr/bin/etcd*
chmod 644 /etc/etcd/ssl/*
mkdir -p /var/lib/etcd/default.etcd
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
```

```
cat >> etcd.conf <<EOF
#[Member]
# !! change me !!
ETCD_NAME="etcd1"
#ETCD_CORS=""
ETCD_DATA_DIR="/var/lib/etcd/default.etcd"
#ETCD_WAL_DIR=""
ETCD_LISTEN_PEER_URLS="https://192.168.0.121:2380"
ETCD_LISTEN_CLIENT_URLS="https://192.168.0.121:2379,http://127.0.0.1:2379"
#ETCD_MAX_SNAPSHOTS="5"
#ETCD_MAX_WALS="5"
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
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://192.168.0.121:2380"
ETCD_ADVERTISE_CLIENT_URLS="https://192.168.0.121:2379"
#ETCD_DISCOVERY=""
#ETCD_DISCOVERY_FALLBACK="proxy"
#ETCD_DISCOVERY_PROXY=""
#ETCD_DISCOVERY_SRV=""
ETCD_INITIAL_CLUSTER="etcd1=https://192.168.0.121:2380,etcd2=https://192.168.0.122:2380,etcd3=https://192.168.0.123:2380"
ETCD_INITIAL_CLUSTER_TOKEN="etcd-cluster"
ETCD_INITIAL_CLUSTER_STATE="new"
#ETCD_STRICT_RECONFIG_CHECK="true"
ETCD_ENABLE_V2="false"
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
EOF
```

3.3版本的etcd service

```
cat >> etcd.service <<EOF
[Unit]
Description=Etcd Server
After=network.target
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
WorkingDirectory=/var/lib/etcd/
EnvironmentFile=-/etc/etcd/etcd.conf
User=etcd
# set GOMAXPROCS to number of processors
ExecStart=/bin/bash -c "GOMAXPROCS=$(nproc) /usr/bin/etcd --name=\"${ETCD_NAME}\" --data-dir=\"${ETCD_DATA_DIR}\" --listen-client-urls=\"${ETCD_LISTEN_CLIENT_URLS}\""
Restart=on-failure
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
```

3.4版本的etcd service，提示 conflicting environment variable "ETCD_NAME" is shadowed by corresponding command-line flag ，是因为3.4版本的etcd启动时候会自动查找ETCD_NAME等环境变量，如果etcd.service也有配置的话，就重复了

```
[Unit]
Description=Etcd Server
After=network.target
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
EnvironmentFile=-/etc/etcd/etcd.conf
ExecStart=/usr/bin/etcd
User=etcd
Restart=on-failure
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```



#### 安装基础服务

master节点安装docker和kube服务，node节点仅安装docker

```
#if docker install before, remove first
# yum remove docker-ce -y
# rm -rf /var/lib/docker
# yum remove kubeadm kubectl kubelet kubernetes-cni -y
# rm -rf /var/lib/kubelet/

# install docker
cd k8s/docker
yum localinstall * -y
cat <<EOF>> /etc/docker/daemon.json 
{
  "insecure-registries":["harbor.bbotte.com"]
}
EOF
systemctl enable docker && systemctl start docker

#install kube service
cd
yum localinstall k8s/rpm/* -y
/bin/cp k8s/rpm/kubeadm /usr/bin/kubeadm
mkdir -p /etc/kubernetes/pki
cd k8s/images/
for i in `ls .`;do docker load < $i;done
cd
systemctl enable kubelet
```

##### 仅master01节点

```
mkdir -p /etc/kubernetes/pki
# kubernetes & etcd 用同样的证书
mkdir /etc/kubernetes/ssl
cp /etc/etcd/ssl/etcd.pem /etc/kubernetes/ssl/
cp /etc/etcd/ssl/etcd-key.pem /etc/kubernetes/ssl/
cp /etc/etcd/ssl/ca.pem /etc/kubernetes/ssl/
```

配置kubernetes master节点

```
cat >> config.yaml <<EOF
apiVersion: kubeadm.k8s.io/v1beta1
bootstrapTokens:
- groups:
  - system:bootstrappers:kubeadm:default-node-token
  token: abfw5z.o3v7qcqgrwlj4gr8 # kubeadm token generate
  ttl: 108h0m0s
  usages:
  - signing
  - authentication
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: 192.168.0.120 #api VIP
  bindPort: 6443
nodeRegistration:
  criSocket: /var/run/dockershim.sock
  name: k8sm1                  #master1 name，change me
  taints:
  - effect: NoSchedule
    key: node-role.kubernetes.io/master
---
apiServer:
  timeoutForControlPlane: 4m0s
  CertSANs:
  - etcd1                  #etcd name
  - etcd2
  - etcd3
  - 192.168.0.121          #master IP
  - 192.168.0.122
  - 192.168.0.123
  - 192.168.0.120          #api VIP
  - 127.0.0.1
  - kubernetes
  - kubernetes.default
  - kubernetes.default.svc
  - kubernetes.default.svc.cluster
  - kubernetes.default.svc.cluster.local
  - 10.244.0.1
  - 10.96.0.1
apiVersion: kubeadm.k8s.io/v1beta1
certificatesDir: /etc/kubernetes/pki
clusterName: kubernetes
controlPlaneEndpoint: "192.168.0.120:6443"  #api VIP
controllerManager: {}
dns:
  type: CoreDNS
etcd:
  external:
    endpoints:
    - https://192.168.0.121:2379    #three etcd node
    - https://192.168.0.122:2379
    - https://192.168.0.123:2379
    caFile: /etc/kubernetes/ssl/ca.pem    #same as /etc/etcd/etcd.conf ca
    certFile: /etc/kubernetes/ssl/etcd.pem 
    keyFile: /etc/kubernetes/ssl/etcd-key.pem
imageRepository: registry.cn-hangzhou.aliyuncs.com/google_containers #your define docker registry
kind: ClusterConfiguration
kubernetesVersion: v1.13.3    #k8s version
networking:
  dnsDomain: cluster.local
  podSubnet: "10.244.0.0/17"   #pod ip address segment,every server has a ip segment, this network segment supports up to 127 hosts.
  serviceSubnet: 10.96.0.0/19 #service ip address segment,this network segment supports up to 8190 services.
scheduler: {}
---
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: "ipvs"
---
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
clusterDNS:
- 10.96.0.10
EOF
```

```
kubeadm init --config k8s/config.yaml
cp k8s/config.yaml /etc/kubernetes/
#保存最后生成的 kubeadm join
kubeadm join --token z2dbca.pe313xd0XXXX 192.168.0.120:6443 --discovery-token-ca-cert-hash sha256:c392bXXXX

mkdir -p $HOME/.kube
/bin/cp /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config
kubectl get cs
kubectl apply -f k8s/network/kubeadm-kuberouter-all-features.yaml
sleep 30
kubectl get po -n kube-system

# copy cert
scp -r /etc/kubernetes/ssl/ k8sm2:/etc/kubernetes/ssl/
scp -r /etc/kubernetes/ssl/ k8sm3:/etc/kubernetes/ssl/

scp /etc/kubernetes/pki/* k8sm2:/etc/kubernetes/pki/
scp /etc/kubernetes/config.yaml k8sm2:/etc/kubernetes/
scp /etc/kubernetes/pki/* k8sm3:/etc/kubernetes/pki/
scp /etc/kubernetes/config.yaml k8sm3:/etc/kubernetes/
```

##### k8s master2 和 master3 

###### 需要修改 /etc/kubernetes/config.yaml 的 nodeRegistration  name，即主机名称

```
kubeadm init --config /etc/kubernetes/config.yaml
```

#### k8s master1

```
docker run --privileged -v /lib/modules:/lib/modules --net=host registry.cn-hangzhou.aliyuncs.com/google_containers/kube-proxy:v1.13.3 kube-proxy --cleanup
kubectl -n kube-system delete ds kube-proxy
sleep 20
kubectl get po -n kube-system
kubectl scale --replicas=3 deployment/coredns -n kube-system
kubectl get po -n kube-system
```



#### node安装步骤

初始化同上

安装docker

```
yum install centos-release-gluster -y
yum install glusterfs-fuse -y
yum localinstall k8s/node/docker/* -y
systemctl enable docker && systemctl start docker
yum localinstall k8s/node/rpm/* -y
cat > /etc/docker/daemon.json <<EOF
{
  "insecure-registries":["harbor.bbotte.com"]
}
EOF
systemctl restart docker
cd k8s/node/images/
for i in `ls .`;do docker load < $i;done
cd
/bin/cp k8s/rpm/kubeadm /usr/bin/kubeadm
systemctl enable kubelet

docker login harbor.bbotte.com -u admin -p hello\!\@\%\^\&123
```

执行master节点 kubeadm init 后的结果加入k8s集群

```
kubeadm join --token b2dbca.pe35XXXXX 192.168.0.120:6443 --discovery-token-ca-cert-hash sha256:c392b12260XXXX
```



master1节点：

#### traefik安装

```
kubectl apply -f k8s/traefik/
```

#### dashboard安装

```
kubectl apply -f k8s/dashboard/
cd k8s/dashboard
grep 'client-certificate-data' ~/.kube/config | head -n 1 | awk '{print $2}' | base64 -d > kubecfg.crt
grep 'client-key-data' ~/.kube/config | head -n 1 | awk '{print $2}' | base64 -d > kubecfg.key

openssl pkcs12 -export -clcerts -inkey kubecfg.key -in kubecfg.crt -out kubecfg.p12 -name "kubernetes-dashboard"

kubectl create serviceaccount dashboard -n default
kubectl create clusterrolebinding dashboard-admin -n default --clusterrole=cluster-admin  --serviceaccount=default:dashboard
kubectl get secret $(kubectl get serviceaccount dashboard -o jsonpath="{.secrets[0].name}") -o jsonpath="{.data.token}" | base64 --decode
cd

登录密码：
```

dashboard web：

https://1.5.1.2:6443/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview?namespace=default

#### 监控

```
kubectl apply -f k8s/metrics/
```

#### harbor auth 略

#### nginx+keepalived 略

#### glusterfs安装 略

#### mysql MHA 略

#### dnsmasq 略