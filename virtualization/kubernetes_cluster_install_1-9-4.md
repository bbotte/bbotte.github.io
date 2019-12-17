---
layout: default
---

## kubernetes集群安装步骤(Version:1.9.4)

###### 备注：centos 7.4 最小化安装

##### 系统设置

| VIP             | 功能                     | 端口映射      |
| --------------- | ---------------------- | --------- |
| 172.16.11.15/32 | kube-Api端口，用于dashboard | 6443:6443 |
| 172.16.11.16/32 | Node高可用端口，用于web访问      | 8880:80   |
| 172.16.11.17/32 | mysql MHA              | 3306:3306 |

设置主机名称(IP和主机名根据实际情况改动)

```
hostnamectl --static set-hostname k8smaster01
exec $SHELL
cat <<EOF >> /etc/hosts
172.16.11.1  k8smaster01
172.16.11.2  k8smaster02
172.16.11.3  k8smaster03
172.16.11.4  k8snode01
172.16.11.5  k8snode02
172.16.11.6  k8snode03
172.16.11.7  k8snode04
172.16.11.8  keepalive01
172.16.11.9  keepalive02
172.16.11.10  gfs01
172.16.11.11  gfs02
172.16.11.12  mysql01
172.16.11.13  mysql02
172.16.11.14  monitor01
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
sysctl -p /etc/sysctl.conf
/sbin/sysctl -p
```

配置DNS服务(可选)

如果数据库在kubernetes集群外部，需要配置DNS服务，比如在2台gfs主机安装

```
yum install dnsmasq -y
sed -i '111 alisten-address=172.16.11.10' /etc/dnsmasq.conf
cat > /etc/dnsmasq.d/dns.conf <<EOF
address=/db-com/172.16.11.17
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
> nameserver 172.16.11.10
> nameserver 172.16.11.11
> EOF
cat >> /etc/sysconfig/network-scripts/ifcfg-eth0 <<EOF
DNS1="172.16.11.10"
DNS2="172.16.11.11"
EOF
```



#### 设置kube_api_VIP(IP和主机名根据实际情况改动)

```
yum install keepalived ipvsadm -y
cp /etc/keepalived/keepalived.conf{,.def}
cat > /etc/keepalived/keepalived.conf <<EOF
! Configuration File for keepalived
 
global_defs {
   notification_email {
      517766237@qq.com
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
    interface ens160        #network card
    virtual_router_id 51
    priority 100            #Weight, configure different values, the other two are 99,98
    advert_int 1 
    mcast_src_ip 172.16.11.1 # local host ip
    authentication {
        auth_type PASS
        auth_pass bbotte_com
    }
    unicast_peer {
        172.16.11.2   #The other party's ip
        172.16.11.3
    }
    virtual_ipaddress {
        172.16.11.15/32     #VIP
    }
    track_script {
        CheckK8sMaster    
    }
}
EOF
systemctl enable keepalived && systemctl restart keepalived
yum install ipvsadm -y
ipvsadm -Ln
ip a
```

#### 生成证书(仅需其中一台，在master1操作)

```
tar -xf k8s1.9.4.tar.gz
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
    "172.16.11.1",
    "172.16.11.2",
    "172.16.11.3",
    "172.16.11.15"
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
        "expiry": "262800h"
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
  "CN": "ca"
}
EOF
cd k8s/ssl/conf/
cfssl gencert --initca=true etcd-root-ca-csr.json | cfssljson --bare ca
cfssl gencert --ca ca.pem --ca-key ca-key.pem --config etcd-gencert.json etcd-csr.json | cfssljson --bare etcd
```

```
for i in k8smaster01 k8smaster02 k8smaster03 ;do ssh ${i} mkdir -p /etc/etcd/ssl; scp etcd-key.pem etcd.pem ca.pem ${i}:/etc/etcd/ssl;done
cd
```

#### etcd集群创建(IP和主机名根据实际情况改动)

```
rpm -ivh k8s/etcd/etcd-3.2.15-1.el7.x86_64.rpm
cp /etc/etcd/etcd.conf{,.def}
cat > /etc/etcd/etcd.conf <<EOF
#[Member]
#ETCD_CORS=""
ETCD_DATA_DIR="/var/lib/etcd/"
#ETCD_WAL_DIR=""
#local server IP
ETCD_LISTEN_PEER_URLS="https://172.16.11.1:2380"
#local server IP
ETCD_LISTEN_CLIENT_URLS="https://172.16.11.1:2379,http://127.0.0.1:2379"
#ETCD_MAX_SNAPSHOTS="5"
#ETCD_MAX_WALS="5"
#change me
ETCD_NAME="etcd01"
#[Clustering]
#local server IP
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://172.16.11.1:2380"
#local server IP
ETCD_ADVERTISE_CLIENT_URLS="https://172.16.11.1:2379"
#cluster server IP
ETCD_INITIAL_CLUSTER="etcd01=https://172.16.11.1:2380,etcd02=https://172.16.11.2:2380,etcd03=https://172.16.11.3:2380" 
ETCD_INITIAL_CLUSTER_TOKEN="etcd-cluster"
ETCD_INITIAL_CLUSTER_STATE="new"
#ETCD_STRICT_RECONFIG_CHECK="true"
#ETCD_ENABLE_V2="true"
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
#[Logging]
#[Unsafe]
#[Version]
#[Profiling]
#[Auth]
EOF
chmod 644 /etc/etcd/ssl/*
systemctl daemon-reload
systemctl enable etcd
systemctl start etcd
export ETCDCTL_API=3

```

#### 安装基础服务

安装docker服务

```
yum localinstall k8s/docker/* -y
systemctl enable docker && systemctl start docker
yum localinstall k8s/rpm/* -y
mkdir -p /etc/kubernetes/pki
cd k8s/images/
for i in `ls .`;do docker load < $i;done
cd
systemctl enable kubelet

rm -f /etc/docker/daemon.json
cat >> /etc/docker/daemon.json <<EOF
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "insecure-registries":["hub.bbotte.com"]
}
EOF
systemctl restart docker

docker login hub.bbotte.com -u admin -p bbotte\@\%\^\&

docker pull hub.bbotte.com/k8s/traefik:latest
docker pull hub.bbotte.com/k8s/busybox
docker pull hub.bbotte.com/k8s/kube-router
docker pull hub.bbotte.com/k8s/heapster-amd64:v1.4.2
docker pull hub.bbotte.com/k8s/heapster-grafana-amd64:v4.4.3
docker pull hub.bbotte.com/k8s/heapster-influxdb-amd64:v1.3.3

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
cat > /etc/kubernetes/config.yaml <<EOF
apiVersion: kubeadm.k8s.io/v1alpha1
kind: MasterConfiguration
etcd:
  endpoints:
  - https://172.16.11.1:2379    #three master node
  - https://172.16.11.2:2379
  - https://172.16.11.3:2379
  caFile: /etc/etcd/ssl/ca.pem  #same as etcd ca
  certFile: /etc/etcd/ssl/etcd.pem 
  keyFile: /etc/etcd/ssl/etcd-key.pem
  dataDir: /var/lib/etcd
networking:
  podSubnet: 10.244.0.0/20
kubernetesVersion: 1.9.4
api:
  advertiseAddress: "172.16.11.15"   #kube-api VIP
token: "dadbca.8q2ncxd0ec6986da"
tokenTTL: "0s"
apiServerCertSANs:
- etcd01
- etcd02
- etcd03
- 172.16.11.1
- 172.16.11.2
- 172.16.11.3
- 172.16.11.15
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
EOF

kubeadm init --config /etc/kubernetes/config.yaml
#保存最后生成的 kubeadm join
kubeadm join --token dadbca.8q2ncxd0ec6986da 172.16.11.15:6443 --discovery-token-ca-cert-hash sha256:c0p2b1226423dcc3ba03e30c52e744533e68754733674443e0cae1a76ea0023a

mkdir -p $HOME/.kube
/bin/cp /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config
kubectl get cs
kubectl create -f k8s/network/kubeadm-kuberouter-all-features.yaml
sleep 60
kubectl get po -n kube-system
kubectl -n kube-system delete ds kube-proxy
docker run --privileged --net=host gcr.io/google_containers/kube-proxy-amd64:v1.9.4 kube-proxy --cleanup-iptables

kubectl get po -n kube-system
scp -r /etc/kubernetes/ssl/ k8smaster02:/etc/kubernetes/ssl/
scp -r /etc/kubernetes/ssl/ k8smaster03:/etc/kubernetes/ssl/

scp /etc/kubernetes/pki/* k8smaster02:/etc/kubernetes/pki/
scp /etc/kubernetes/config.yaml k8smaster02:/etc/kubernetes/
scp /etc/kubernetes/pki/* k8smaster03:/etc/kubernetes/pki/
scp /etc/kubernetes/config.yaml k8smaster03:/etc/kubernetes/
```

##### k8s master2 和 master3 

```
kubeadm init --config /etc/kubernetes/config.yaml
```

#### k8s master1

```
kubectl -n kube-system delete ds kube-proxy
kubectl scale --replicas=3 deployment/coredns -n kube-system
kubectl get po -n kube-system
```



#### node安装步骤

初始化同上

安装docker

```
yum install glusterfs-fuse -y
tar -xf k8s1.9node.tar.gz
yum localinstall node/docker/* -y
systemctl enable docker && systemctl start docker
yum localinstall node/rpm/* -y
cat > /etc/docker/daemon.json <<EOF
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "insecure-registries":["hub.bbotte.com"]
}
EOF
systemctl restart docker
cd node/images/
for i in `ls .`;do docker load < $i;done
cd
systemctl enable kubelet

docker login hub.bbotte.com -u admin -p bbotte\@\%\^\&

docker pull hub.bbotte.com/k8s/traefik:latest
docker pull hub.bbotte.com/k8s/busybox
docker pull hub.bbotte.com/k8s/kube-router
#docker pull hub.bbotte.com/k8s/kube-router:v0.1.0
docker pull hub.bbotte.com/k8s/heapster-amd64:v1.4.2
docker pull hub.bbotte.com/k8s/heapster-grafana-amd64:v4.4.3
docker pull hub.bbotte.com/k8s/heapster-influxdb-amd64:v1.3.3
docker pull hub.bbotte.com/k8s/kubernetes-dashboard-amd64:v1.8.3
```

执行master节点 kubeadm init 后的结果加入k8s集群

```
kubeadm join --token dadbca.8q2ncxd0ec6986da 172.16.11.15:6443 --discovery-token-ca-cert-hash sha256:c0p2b1226423dcc3ba03e30c52e744533e68754733674443e0cae1a76ea0023a
```



master1节点：

#### traefik安装

```
kubectl create -f k8s/traefik/
```

#### dashboard安装

```
kubectl create -f k8s/dashboard/kubernetes-dashboard.yaml
cd k8s/dashboard
grep 'client-certificate-data' ~/.kube/config | head -n 1 | awk '{print $2}' | base64 -d > kubecfg.crt
grep 'client-key-data' ~/.kube/config | head -n 1 | awk '{print $2}' | base64 -d > kubecfg.key

openssl pkcs12 -export -clcerts -inkey kubecfg.key -in kubecfg.crt -out kubecfg.p12 -name "kubernetes-bbotte"

kubectl create serviceaccount dashboard -n default
kubectl create clusterrolebinding dashboard-admin -n default --clusterrole=cluster-admin  --serviceaccount=default:dashboard
kubectl get secret $(kubectl get serviceaccount dashboard -o jsonpath="{.secrets[0].name}") -o jsonpath="{.data.token}" | base64 --decode
cd


登录密码：
XXXX
```

dashboard web：

https://1.1.1.1:6443/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview?namespace=default

#### heapster监控

```
kubectl create -f k8s/monitor/
```

#### harbor auth 略

#### nginx+keepalived 略

#### glusterfs安装 略

#### mysql MHA 略

#### dnsmasq 略

#### 用户环境配置

```
保证gfs，redis，mysql正常
frontend端口根据客户提供端口修改
```

