---
layout: default
---

# linux工匠之ceph存储集群实验

1. [ceph存储集群实验](http://www.bbotte.com/server-config/ceph-storage-cluster-experiment/#ceph)
2. [集群主机初始化](http://www.bbotte.com/server-config/ceph-storage-cluster-experiment/#i)
3. [创建集群](http://www.bbotte.com/server-config/ceph-storage-cluster-experiment/#i-2)
4. [配置初始 monitor](http://www.bbotte.com/server-config/ceph-storage-cluster-experiment/#_monitor)
5. [部署OSD节点](http://www.bbotte.com/server-config/ceph-storage-cluster-experiment/#OSD)
6. [激活OSD](http://www.bbotte.com/server-config/ceph-storage-cluster-experiment/#OSD-2)
7. [添加元数据服务器](http://www.bbotte.com/server-config/ceph-storage-cluster-experiment/#i-3)
8. [添加RGW配置](http://www.bbotte.com/server-config/ceph-storage-cluster-experiment/#RGW)
9. [测试集群](http://www.bbotte.com/server-config/ceph-storage-cluster-experiment/#i-4)
10. [ceph块设备](http://www.bbotte.com/server-config/ceph-storage-cluster-experiment/#ceph-2)
11. [文件系统](http://www.bbotte.com/server-config/ceph-storage-cluster-experiment/#i-5)
12. [对象存储](http://www.bbotte.com/server-config/ceph-storage-cluster-experiment/#i-6)
13. [ceph S3接口](http://www.bbotte.com/server-config/ceph-storage-cluster-experiment/#ceph_S3)

### **ceph存储集群实验**

Ceph is a unified, distributed storage system designed for excellent performance, reliability and scalability.

Ceph集群可以为我们提供**对象存储和块设备**，如果要使用RESTful API，需要安装**对象网关**，支持S3和swift接口
**对象存储**，块设备和文件存储的结合，也就是通常意义的键值存储，其接口就是简单的GET、PUT、DEL和其他扩展，如S3、七牛、Swift
**块设备**简单理解，比如VMware虚拟机添加一块磁盘，实际上是在磁盘上创建了一个文件；Xen或KVM可以通过qemu-img创建一个qcow2或者img文件用于做虚拟机系统盘，或者是一个DVD光盘、磁盘阵列、硬盘，是映射给主机用
**文件存储**可以这么理解，比如Samba服务、NFS服务、FTP服务、GFS、HDFS，是用于做存储的服务，直接挂载就可以用，不用格式化

ceph存储结构：

Ceph 存储集群至少需要**一个 Ceph Monitor 和两个 OSD 守护进程**。而运行 Ceph 文件系统客户端时，则必须要有**元数据服务器**（ Metadata Server ）。
Ceph OSDs: Ceph **OSD 守护进程**（ Ceph OSD ）的功能是存储数据，处理数据的复制、恢复、回填、再均衡，并通过检查其他OSD 守护进程的心跳来向 Ceph Monitors 提供一些监控信息。当 Ceph 存储集群设定为有2个副本时，至少需要2个 OSD 守护进程，集群才能达到 active+clean 状态（ Ceph 默认有3个副本，但你可以调整副本数）。
**Monitors**: Ceph Monitor维护着展示集群状态的各种图表，包括监视器图、 OSD 图、归置组（ PG ）图、和 CRUSH 图。 Ceph 保存着发生在Monitors 、 OSD 和 PG上的每一次状态变更的历史信息（称为 epoch ）。
**MDSs**: Ceph 元数据服务器（ MDS ）为 Ceph 文件系统存储元数据（也就是说，Ceph 块设备和 Ceph 对象存储不使用MDS ）。元数据服务器使得 POSIX 文件系统的用户们，可以在不对 Ceph 存储集群造成负担的前提下，执行诸如 ls、find 等基本命令

ceph官网：[https://ceph.com](https://ceph.com/)

ceph官方文档：[http://docs.ceph.org.cn](http://docs.ceph.org.cn/)

使用ceph前需要了解其结构和运行模式，因为ceph和其他软件设计思维还是不同的，下面按照官方思路实验

<https://www.ibm.com/developerworks/cn/linux/l-ceph/>

<https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/>

<https://www.cac.cornell.edu/education/Ceph.pdf>

```
admin-node         
ceph-deploy 
    |                 node1
    |---------------> mon.node1
    |
    |
    | --------------> node2
    |                 osd.0
    |
    | --------------> node3
                      osd.1
```

上述为admin、node1、node2、node3 总共4个主机节点

### 集群主机初始化

4台主机都需要的操作步骤

```
# cat /etc/centos-release
CentOS Linux release 7.4.1708 (Core)
 
cat <<EOF>> /etc/hosts
192.168.22.163 admin
192.168.22.75 node1
192.168.22.76 node2
192.168.22.77 node3
EOF
hostnamectl --static set-hostname admin/node1/node2/node3
exec $SHELL
ntpdate ntp1.aliyun.com
systemctl stop firewalld
systemctl disable firewalld
sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config 
setenforce 0
yum install yum-plugin-priorities deltarpm epel-release -y
```

下面只是ceph-deploy主机的操作步骤，3个node节点不需要操作，ceph-deploy 可理解为ansible或puppet，是ceph集群管理工具
admin节点：

```
cat <<EOF>> /etc/yum.repos.d/ceph.repo
[Ceph-noarch]
name=Ceph noarch packages
baseurl=http://download.ceph.com/rpm-jewel/el7/noarch
enabled=1
gpgcheck=1
type=rpm-md
gpgkey=https://download.ceph.com/keys/release.asc
priority=1
EOF
yum install ceph-deploy -y
rm -f /etc/yum.repos.d/ceph.repo
```

admin-node生成公钥，保证可以无密码登录3个node

```
ssh-keygen -t rsa
ssh-copy-id node1/node2/node3
```

### **创建集群**

tips：
如果在某些地方碰到麻烦，想从头再来，可以用下列命令清除配置：

```
ceph-deploy purgedata {ceph-node} [{ceph-node}]
ceph-deploy forgetkeys
```

用下列命令可以连 Ceph 安装包一起清除：

```
ceph-deploy purge {ceph-node} [{ceph-node}]
```

如果执行了 purge ，你必须重新安装 Ceph

```
    -^-
   /   \
   |O o|  ceph-deploy v1.5.39
   ).-.(
  '/|||`
  | '|` |
    '|`
```

创建集群

```
# mkdir cluster && cd cluster/
# ceph-deploy new node1
[ceph_deploy.conf][DEBUG ] found configuration file at: /root/.cephdeploy.conf
[ceph_deploy.cli][INFO  ] Invoked (1.5.39): /usr/bin/ceph-deploy new node1
[ceph_deploy.cli][INFO  ] ceph-deploy options:
[ceph_deploy.cli][INFO  ]  username                      : None
[ceph_deploy.cli][INFO  ]  func                          : <function new at 0x16fc500>
[ceph_deploy.cli][INFO  ]  verbose                       : False
[ceph_deploy.cli][INFO  ]  overwrite_conf                : False
[ceph_deploy.cli][INFO  ]  quiet                         : False
[ceph_deploy.cli][INFO  ]  cd_conf                       : <ceph_deploy.conf.cephdeploy.Conf instance at 0x176e5f0>
[ceph_deploy.cli][INFO  ]  cluster                       : ceph
[ceph_deploy.cli][INFO  ]  ssh_copykey                   : True
[ceph_deploy.cli][INFO  ]  mon                           : ['node1']
[ceph_deploy.cli][INFO  ]  public_network                : None
[ceph_deploy.cli][INFO  ]  ceph_conf                     : None
[ceph_deploy.cli][INFO  ]  cluster_network               : None
[ceph_deploy.cli][INFO  ]  default_release               : False
[ceph_deploy.cli][INFO  ]  fsid                          : None
[ceph_deploy.new][DEBUG ] Creating new cluster named ceph
[ceph_deploy.new][INFO  ] making sure passwordless SSH succeeds
[node1][DEBUG ] connected to host: admin 
[node1][INFO  ] Running command: ssh -CT -o BatchMode=yes node1
[node1][DEBUG ] connected to host: node1 
[node1][DEBUG ] detect platform information from remote host
[node1][DEBUG ] detect machine type
[node1][DEBUG ] find the location of an executable
[node1][INFO  ] Running command: /usr/sbin/ip link show
[node1][INFO  ] Running command: /usr/sbin/ip addr show
[node1][DEBUG ] IP addresses found: [u'172.17.0.1', u'192.168.22.75']
[ceph_deploy.new][DEBUG ] Resolving host node1
[ceph_deploy.new][DEBUG ] Monitor node1 at 192.168.22.75
[ceph_deploy.new][DEBUG ] Monitor initial members are ['node1']
[ceph_deploy.new][DEBUG ] Monitor addrs are ['192.168.22.75']
[ceph_deploy.new][DEBUG ] Creating a random mon key...
[ceph_deploy.new][DEBUG ] Writing monitor keyring to ceph.mon.keyring...
[ceph_deploy.new][DEBUG ] Writing initial config to ceph.conf...
[root@admin cluster]# 
[root@admin cluster]# ls
ceph.conf  ceph-deploy-ceph.log  ceph.mon.keyring
```

把 Ceph 配置文件里的默认副本数从 3 改成 2 ，这样只有两个 OSD 也可以达到 active + clean 状态

```
# cat <<EOF>> ceph.conf
osd pool default size = 2
EOF
```

把ceph安装到各节点

```
# ceph-deploy install admin node1 node2 node3
```

下面是安装node1节点的日志，日志有删减

```
[root@admin cluster]# ceph-deploy install node1
[ceph_deploy.conf][DEBUG ] found configuration file at: /root/.cephdeploy.conf
[ceph_deploy.cli][INFO  ] Invoked (1.5.39): /usr/bin/ceph-deploy install node1
[ceph_deploy.install][DEBUG ] Installing stable version jewel on cluster ceph hosts node1
[ceph_deploy.install][DEBUG ] Detecting platform for host node1 ...
[node1][DEBUG ] connected to host: node1 
[node1][DEBUG ] detect platform information from remote host
[node1][DEBUG ] detect machine type
[ceph_deploy.install][INFO  ] Distro info: CentOS Linux 7.4.1708 Core
[node1][INFO  ] installing Ceph on node1
[node1][INFO  ] Running command: yum clean all
[node1][INFO  ] Running command: yum -y install epel-release
[node1][INFO  ] Running command: yum -y install yum-plugin-priorities
[node1][INFO  ] Running command: yum install -y https://download.ceph.com/rpm-jewel/el7/noarch/ceph-release-1-0.el7.noarch.rpm
[node1][DEBUG ] Loaded plugins: fastestmirror, priorities
[node1][DEBUG ] Examining /var/tmp/yum-root-cHdydw/ceph-release-1-0.el7.noarch.rpm: ceph-release-1-1.el7.noarch
[node1][DEBUG ] Marking /var/tmp/yum-root-cHdydw/ceph-release-1-0.el7.noarch.rpm to be installed
[node1][DEBUG ] Resolving Dependencies
[node1][DEBUG ] --> Running transaction check
[node1][DEBUG ] ---> Package ceph-release.noarch 0:1-1.el7 will be installed
[node1][DEBUG ] --> Finished Dependency Resolution
[node1][DEBUG ] 
[node1][DEBUG ] Installed:
[node1][DEBUG ]   ceph-release.noarch 0:1-1.el7                                                 
[node1][DEBUG ] Complete!
[node1][WARNIN] ensuring that /etc/yum.repos.d/ceph.repo contains a high priority
[node1][WARNIN] altered ceph.repo priorities to contain: priority=1
[node1][INFO  ] Running command: yum -y install ceph ceph-radosgw
[node1][DEBUG ] 12 packages excluded due to repository priority protections
[node1][DEBUG ] Resolving Dependencies
[node1][DEBUG ] Dependencies Resolved
[node1][DEBUG ] 
[node1][DEBUG ] ================================================================================
[node1][DEBUG ]  Package              Arch           Version                 Repository    Size
[node1][DEBUG ] ================================================================================
[node1][DEBUG ] Installing:
[node1][DEBUG ]  ceph                 x86_64         1:10.2.10-0.el7         Ceph         3.0 k
[node1][DEBUG ]  ceph-radosgw         x86_64         1:10.2.10-0.el7         Ceph         266 k
[node1][DEBUG ] Installing for dependencies:
[node1][DEBUG ]  ceph-base            x86_64         1:10.2.10-0.el7         Ceph         4.2 M
[node1][DEBUG ]  ceph-common          x86_64         1:10.2.10-0.el7         Ceph          17 M
[node1][DEBUG ]  ceph-mds             x86_64         1:10.2.10-0.el7         Ceph         2.8 M
[node1][DEBUG ]  ceph-mon             x86_64         1:10.2.10-0.el7         Ceph         2.8 M
[node1][DEBUG ]  ceph-osd             x86_64         1:10.2.10-0.el7         Ceph         9.1 M
[node1][DEBUG ]  ceph-selinux         x86_64         1:10.2.10-0.el7         Ceph          20 k
[node1][DEBUG ] 
[node1][DEBUG ] Transaction Summary
[node1][DEBUG ] ================================================================================
[node1][DEBUG ] Install  2 Packages (+6 Dependent packages)
[node1][DEBUG ] 
[node1][DEBUG ] Installed:
[node1][DEBUG ]   ceph.x86_64 1:10.2.10-0.el7        ceph-radosgw.x86_64 1:10.2.10-0.el7       
[node1][DEBUG ] 
[node1][DEBUG ] Dependency Installed:
[node1][DEBUG ]   ceph-base.x86_64 1:10.2.10-0.el7      ceph-common.x86_64 1:10.2.10-0.el7      
[node1][DEBUG ]   ceph-mds.x86_64 1:10.2.10-0.el7       ceph-mon.x86_64 1:10.2.10-0.el7         
[node1][DEBUG ]   ceph-osd.x86_64 1:10.2.10-0.el7       ceph-selinux.x86_64 1:10.2.10-0.el7     
[node1][DEBUG ] 
[node1][DEBUG ] Complete!
[node1][INFO  ] Running command: ceph --version
[node1][DEBUG ] ceph version 10.2.10 (5dc1e4c05cb68dbf62ae6fce3f0700e4654fdbbe
```

上面的步骤中有 yum clean all，因为yum安装rpm包超时出错了几次，于是乎手动yum安装所需的包，
安装完成后查看

```
/etc/yum.repos.d/ceph.repo
 
[Ceph]
name=Ceph packages for $basearch
baseurl=http://download.ceph.com/rpm-jewel/el7/$basearch
enabled=1
gpgcheck=1
type=rpm-md
gpgkey=https://download.ceph.com/keys/release.asc
priority=1
 
[Ceph-noarch]
name=Ceph noarch packages
baseurl=http://download.ceph.com/rpm-jewel/el7/noarch
enabled=1
gpgcheck=1
type=rpm-md
gpgkey=https://download.ceph.com/keys/release.asc
priority=1
 
[ceph-source]
name=Ceph source packages
baseurl=http://download.ceph.com/rpm-jewel/el7/SRPMS
enabled=1
gpgcheck=1
type=rpm-md
gpgkey=https://download.ceph.com/keys/release.asc
priority=1
```

### 配置初始 monitor

并收集所有密钥，我们放到node1这个节点主机

```
# ceph-deploy mon create-initial
[ceph_deploy.conf][DEBUG ] found configuration file at: /root/.cephdeploy.conf
[ceph_deploy.cli][INFO  ] Invoked (1.5.39): /usr/bin/ceph-deploy mon create-initial
[ceph_deploy.mon][DEBUG ] Deploying mon, cluster ceph hosts node1
[ceph_deploy.mon][DEBUG ] detecting platform for host node1 ...
[node1][DEBUG ] connected to host: node1 
[node1][DEBUG ] detect platform information from remote host
[node1][DEBUG ] detect machine type
[node1][DEBUG ] find the location of an executable
[ceph_deploy.mon][INFO  ] distro info: CentOS Linux 7.4.1708 Core
[node1][DEBUG ] determining if provided host has same hostname in remote
[node1][DEBUG ] get remote short hostname
[node1][DEBUG ] deploying mon to node1
[node1][DEBUG ] get remote short hostname
[node1][DEBUG ] remote hostname: node1
[node1][DEBUG ] write cluster configuration to /etc/ceph/{cluster}.conf
[node1][DEBUG ] create the mon path if it does not exist
[node1][DEBUG ] checking for done path: /var/lib/ceph/mon/ceph-node1/done
[node1][DEBUG ] done path does not exist: /var/lib/ceph/mon/ceph-node1/done
[node1][INFO  ] creating keyring file: /var/lib/ceph/tmp/ceph-node1.mon.keyring
[node1][DEBUG ] create the monitor keyring file
[node1][INFO  ] Running command: ceph-mon --cluster ceph --mkfs -i node1 --keyring /var/lib/ceph/tmp/ceph-node1.mon.keyring --setuser 167 --setgroup 167
[node1][DEBUG ] ceph-mon: mon.noname-a 192.168.22.75:6789/0 is local, renaming to mon.node1
[node1][DEBUG ] ceph-mon: set fsid to c0c55799-7178-41aa-804e-6e900331f900
[node1][DEBUG ] ceph-mon: created monfs at /var/lib/ceph/mon/ceph-node1 for mon.node1
[node1][INFO  ] unlinking keyring file /var/lib/ceph/tmp/ceph-node1.mon.keyring
[node1][DEBUG ] create a done file to avoid re-doing the mon deployment
[node1][DEBUG ] create the init path if it does not exist
[node1][INFO  ] Running command: systemctl enable ceph.target
[node1][INFO  ] Running command: systemctl enable ceph-mon@node1
[node1][WARNIN] Created symlink from /etc/systemd/system/ceph-mon.target.wants/ceph-mon@node1.service to /usr/lib/systemd/system/ceph-mon@.service.
[node1][INFO  ] Running command: systemctl start ceph-mon@node1
[node1][INFO  ] Running command: ceph --cluster=ceph --admin-daemon /var/run/ceph/ceph-mon.node1.asok mon_status
[node1][DEBUG ] ********************************************************************************
[node1][DEBUG ] status for monitor: mon.node1
[node1][DEBUG ] {
[node1][DEBUG ]   "election_epoch": 3, 
[node1][DEBUG ]   "extra_probe_peers": [], 
[node1][DEBUG ]   "monmap": {
[node1][DEBUG ]     "created": "2018-01-30 16:37:24.272258", 
[node1][DEBUG ]     "epoch": 1, 
[node1][DEBUG ]     "fsid": "c0c55799-7178-41aa-804e-6e900331f900", 
[node1][DEBUG ]     "modified": "2018-01-30 16:37:24.272258", 
[node1][DEBUG ]     "mons": [
[node1][DEBUG ]       {
[node1][DEBUG ]         "addr": "192.168.22.75:6789/0", 
[node1][DEBUG ]         "name": "node1", 
[node1][DEBUG ]         "rank": 0
[node1][DEBUG ]       }
[node1][DEBUG ]     ]
[node1][DEBUG ]   }, 
[node1][DEBUG ]   "name": "node1", 
[node1][DEBUG ]   "outside_quorum": [], 
[node1][DEBUG ]   "quorum": [
[node1][DEBUG ]     0
[node1][DEBUG ]   ], 
[node1][DEBUG ]   "rank": 0, 
[node1][DEBUG ]   "state": "leader", 
[node1][DEBUG ]   "sync_provider": []
[node1][DEBUG ] }
[node1][DEBUG ] ********************************************************************************
[node1][INFO  ] monitor: mon.node1 is running
[node1][INFO  ] Running command: ceph --cluster=ceph --admin-daemon /var/run/ceph/ceph-mon.node1.asok mon_status
[ceph_deploy.mon][INFO  ] processing monitor mon.node1
[node1][DEBUG ] connected to host: node1 
[node1][DEBUG ] detect platform information from remote host
[node1][DEBUG ] detect machine type
[node1][DEBUG ] find the location of an executable
[node1][INFO  ] Running command: ceph --cluster=ceph --admin-daemon /var/run/ceph/ceph-mon.node1.asok mon_status
[ceph_deploy.mon][INFO  ] mon.node1 monitor has reached quorum!
[ceph_deploy.mon][INFO  ] all initial monitors are running and have formed quorum
[ceph_deploy.mon][INFO  ] Running gatherkeys...
[ceph_deploy.gatherkeys][INFO  ] Storing keys in temp directory /tmp/tmpLsdKh5
[node1][DEBUG ] connected to host: node1 
[node1][DEBUG ] detect platform information from remote host
[node1][DEBUG ] detect machine type
[node1][DEBUG ] get remote short hostname
[node1][DEBUG ] fetch remote file
[node1][INFO  ] Running command: /usr/bin/ceph --connect-timeout=25 --cluster=ceph --admin-daemon=/var/run/ceph/ceph-mon.node1.asok mon_status
[node1][INFO  ] Running command: /usr/bin/ceph --connect-timeout=25 --cluster=ceph --name mon. --keyring=/var/lib/ceph/mon/ceph-node1/keyring auth get client.admin
[node1][INFO  ] Running command: /usr/bin/ceph --connect-timeout=25 --cluster=ceph --name mon. --keyring=/var/lib/ceph/mon/ceph-node1/keyring auth get client.bootstrap-mds
[node1][INFO  ] Running command: /usr/bin/ceph --connect-timeout=25 --cluster=ceph --name mon. --keyring=/var/lib/ceph/mon/ceph-node1/keyring auth get client.bootstrap-mgr
[node1][INFO  ] Running command: /usr/bin/ceph --connect-timeout=25 --cluster=ceph --name mon. --keyring=/var/lib/ceph/mon/ceph-node1/keyring auth get-or-create client.bootstrap-mgr mon allow profile bootstrap-mgr
[node1][INFO  ] Running command: /usr/bin/ceph --connect-timeout=25 --cluster=ceph --name mon. --keyring=/var/lib/ceph/mon/ceph-node1/keyring auth get client.bootstrap-osd
[node1][INFO  ] Running command: /usr/bin/ceph --connect-timeout=25 --cluster=ceph --name mon. --keyring=/var/lib/ceph/mon/ceph-node1/keyring auth get client.bootstrap-rgw
[ceph_deploy.gatherkeys][INFO  ] Storing ceph.client.admin.keyring
[ceph_deploy.gatherkeys][INFO  ] Storing ceph.bootstrap-mds.keyring
[ceph_deploy.gatherkeys][INFO  ] Storing ceph.bootstrap-mgr.keyring
[ceph_deploy.gatherkeys][INFO  ] keyring 'ceph.mon.keyring' already exists
[ceph_deploy.gatherkeys][INFO  ] Storing ceph.bootstrap-osd.keyring
[ceph_deploy.gatherkeys][INFO  ] Storing ceph.bootstrap-rgw.keyring
[ceph_deploy.gatherkeys][INFO  ] Destroy temp directory /tmp/tmpLsdKh5

```

```
[root@node1 ~]# ps aux|grep ceph
ceph      1535  0.5  1.8 328440 18400 ?        Ssl  17:27   0:00 /usr/bin/ceph-mon -f --cluster ceph --id node1 --setuser ceph --setgroup ceph
```

安装完之后就可以看到有ceph的进程运行

当前目录里应该会出现这些密钥环

```
[root@admin cluster]# ls
ceph.bootstrap-mds.keyring  ceph.bootstrap-rgw.keyring  ceph-deploy-ceph.log
ceph.bootstrap-mgr.keyring  ceph.client.admin.keyring   ceph.mon.keyring
ceph.bootstrap-osd.keyring  ceph.conf
```

如上，node1节点的monitor部署完毕，线上环境的话至少需要3个monitor

### 部署OSD节点

下面部署2个OSD节点
登录到 Ceph 节点、并给 OSD 守护进程创建一个目录

```
ssh node2
mkdir /var/local/osd0
exit
 
ssh node3
mkdir /var/local/osd1
exit
```

从管理节点执行 ceph-deploy 来准备 OSD

```
# ceph-deploy osd prepare node2:/var/local/osd0 node3:/var/local/osd1
[ceph_deploy.conf][DEBUG ] found configuration file at: /root/.cephdeploy.conf
[ceph_deploy.cli][INFO  ] Invoked (1.5.39): /usr/bin/ceph-deploy osd prepare node2:/var/local/osd0 node3:/var/local/osd1
[ceph_deploy.cli][INFO  ] ceph-deploy options:
[ceph_deploy.cli][INFO  ]  disk                          : [('node2', '/var/local/osd0', None), ('node3', '/var/local/osd1', None)]
[ceph_deploy.cli][INFO  ]  dmcrypt_key_dir               : /etc/ceph/dmcrypt-keys
[ceph_deploy.osd][DEBUG ] Preparing cluster ceph disks node2:/var/local/osd0: node3:/var/local/osd1:
[node2][DEBUG ] connected to host: node2 
[node2][DEBUG ] detect platform information from remote host
[node2][DEBUG ] detect machine type
[node2][DEBUG ] find the location of an executable
[ceph_deploy.osd][INFO  ] Distro info: CentOS Linux 7.4.1708 Core
[ceph_deploy.osd][DEBUG ] Deploying osd to node2
[node2][DEBUG ] write cluster configuration to /etc/ceph/{cluster}.conf
[node2][WARNIN] osd keyring does not exist yet, creating one
[node2][DEBUG ] create a keyring file
[ceph_deploy.osd][DEBUG ] Preparing host node2 disk /var/local/osd0 journal None activate False
[node2][DEBUG ] find the location of an executable
[node2][INFO  ] Running command: /usr/sbin/ceph-disk -v prepare --cluster ceph --fs-type xfs -- /var/local/osd0
[node2][WARNIN] command: Running command: /usr/bin/ceph-osd --cluster=ceph --show-config-value=fsid
[node2][WARNIN] command: Running command: /usr/bin/ceph-osd --check-allows-journal -i 0 --log-file $run_dir/$cluster-osd-check.log --cluster ceph --setuser ceph --setgroup ceph
[node2][WARNIN] command: Running command: /usr/bin/ceph-osd --check-wants-journal -i 0 --log-file $run_dir/$cluster-osd-check.log --cluster ceph --setuser ceph --setgroup ceph
[node2][WARNIN] command: Running command: /usr/bin/ceph-osd --check-needs-journal -i 0 --log-file $run_dir/$cluster-osd-check.log --cluster ceph --setuser ceph --setgroup ceph
[node2][WARNIN] command: Running command: /usr/bin/ceph-osd --cluster=ceph --show-config-value=osd_journal_size
[node2][WARNIN] populate_data_path: Preparing osd data dir /var/local/osd0
[node2][WARNIN] command: Running command: /usr/sbin/restorecon -R /var/local/osd0/ceph_fsid.22908.tmp
[node2][WARNIN] command: Running command: /usr/bin/chown -R ceph:ceph /var/local/osd0/ceph_fsid.22908.tmp
[node2][WARNIN] command: Running command: /usr/sbin/restorecon -R /var/local/osd0/fsid.22908.tmp
[node2][WARNIN] command: Running command: /usr/bin/chown -R ceph:ceph /var/local/osd0/fsid.22908.tmp
[node2][WARNIN] command: Running command: /usr/sbin/restorecon -R /var/local/osd0/magic.22908.tmp
[node2][WARNIN] command: Running command: /usr/bin/chown -R ceph:ceph /var/local/osd0/magic.22908.tmp
[node2][INFO  ] checking OSD status...
[node2][DEBUG ] find the location of an executable
[node2][INFO  ] Running command: /bin/ceph --cluster=ceph osd stat --format=json
[ceph_deploy.osd][DEBUG ] Host node2 is now ready for osd use.
```

### 激活OSD

```
# ceph-deploy osd activate node2:/var/local/osd0 node3:/var/local/osd1
```

遇到错误

```
[node2][WARNIN]   File "/usr/lib/python2.7/site-packages/ceph_disk/main.py", line 2800, in ceph_osd_mkfs
[node2][WARNIN]     raise Error('%s failed : %s' % (str(arguments), error))
[node2][WARNIN] ceph_disk.main.Error: Error: ['ceph-osd', '--cluster', 'ceph', '--mkfs', '--mkkey', '-i', u'0', '--monmap', '/var/local/osd0/activate.monmap', '--osd-data', '/var/local/osd0', '--osd-journal', '/var/local/osd0/journal', '--osd-uuid', u'2a972ab3-43ef-46c5-833b-84b188b5fcec', '--keyring', '/var/local/osd0/keyring', '--setuser', 'ceph', '--setgroup', 'ceph'] failed : 2018-01-30 16:49:28.077476 7f1cad08c800 -1 filestore(/var/local/osd0) mkfs: write_version_stamp() failed: (13) Permission denied
[node2][WARNIN] 2018-01-30 16:49:28.077502 7f1cad08c800 -1 OSD::mkfs: ObjectStore::mkfs failed with error -13
[node2][WARNIN] 2018-01-30 16:49:28.077556 7f1cad08c800 -1  ** ERROR: error creating empty object store in /var/local/osd0: (13) Permission denied
[node2][WARNIN] 
[node2][ERROR ] RuntimeError: command returned non-zero exit status: 1
[ceph_deploy][ERROR ] RuntimeError: Failed to execute command: /usr/sbin/ceph-disk -v activate --mark-init systemd --mount /var/local/osd0
```

需要修改存储的权限为ceph，如果是磁盘也需要修改权限。原因是官方文档ceph是一个拥有sudo权限的普通用户，而这里我们用的root

```
[root@node2 ~]# chown ceph.ceph -R /var/local/osd0
 
[root@node3 ~]# chown -R ceph.ceph /var/local/osd1
```

再次执行激活操作

```
[ceph_deploy.conf][DEBUG ] found configuration file at: /root/.cephdeploy.conf
[ceph_deploy.cli][INFO  ] Invoked (1.5.39): /usr/bin/ceph-deploy osd activate node2:/var/local/osd0
[ceph_deploy.cli][INFO  ]  disk                          : [('node2', '/var/local/osd0', None)]
[ceph_deploy.osd][DEBUG ] Activating cluster ceph disks node2:/var/local/osd0:
[node2][DEBUG ] connected to host: node2 
[node2][DEBUG ] detect platform information from remote host
[node2][DEBUG ] detect machine type
[node2][DEBUG ] find the location of an executable
[ceph_deploy.osd][INFO  ] Distro info: CentOS Linux 7.4.1708 Core
[ceph_deploy.osd][DEBUG ] activating host node2 disk /var/local/osd0
[ceph_deploy.osd][DEBUG ] will use init type: systemd
[node2][DEBUG ] find the location of an executable
[node2][INFO  ] Running command: /usr/sbin/ceph-disk -v activate --mark-init systemd --mount /var/local/osd0
[node2][WARNIN] main_activate: path = /var/local/osd0
[node2][WARNIN] activate: Cluster uuid is c0c55799-7178-41aa-804e-6e900331f900
[node2][WARNIN] command: Running command: /usr/bin/ceph-osd --cluster=ceph --show-config-value=fsid
[node2][WARNIN] activate: Cluster name is ceph
[node2][WARNIN] activate: OSD uuid is 2a972ab3-43ef-46c5-833b-84b188b5fcec
[node2][WARNIN] activate: OSD id is 0
[node2][WARNIN] activate: Marking with init system systemd
[node2][WARNIN] command: Running command: /usr/sbin/restorecon -R /var/local/osd0/systemd
[node2][WARNIN] command: Running command: /usr/bin/chown -R ceph:ceph /var/local/osd0/systemd
[node2][WARNIN] activate: ceph osd.0 data dir is ready at /var/local/osd0
[node2][WARNIN] start_daemon: Starting ceph osd.0...
[node2][WARNIN] command_check_call: Running command: /usr/bin/systemctl disable ceph-osd@0
[node2][WARNIN] Removed symlink /etc/systemd/system/ceph-osd.target.wants/ceph-osd@0.service.
[node2][WARNIN] command_check_call: Running command: /usr/bin/systemctl disable ceph-osd@0 --runtime
[node2][WARNIN] command_check_call: Running command: /usr/bin/systemctl enable ceph-osd@0
[node2][WARNIN] Created symlink from /etc/systemd/system/ceph-osd.target.wants/ceph-osd@0.service to /usr/lib/systemd/system/ceph-osd@.service.
[node2][WARNIN] command_check_call: Running command: /usr/bin/systemctl start ceph-osd@0
[node2][INFO  ] checking OSD status...
[node2][DEBUG ] find the location of an executable
[node2][INFO  ] Running command: /bin/ceph --cluster=ceph osd stat --format=json
[node2][INFO  ] Running command: systemctl enable ceph.target
```

```
[root@node2 ~]# ps aux|grep ceph
ceph      1738  3.2  2.4 842128 24720 ?        Ssl  17:30   0:00 /usr/bin/ceph-osd -f --cluster ceph --id 0 --setuser ceph --setgroup ceph
```

ceph-deploy 把配置文件和 admin 密钥拷贝到管理节点和 Ceph 节点，这样你每次执行 Ceph 命令行时就无需指定 monitor 地址和 ceph.client.admin.keyring
用法：ceph-deploy admin {admin-node} {ceph-node}

```
# ceph-deploy admin admin node1 node2 node3
```

新加了 OSD ， Ceph集群就开始重均衡，把归置组迁移到新 OSD 。可以用下面的 ceph 命令观察此过程

```
# ceph -w
    cluster c0c55799-7178-41aa-804e-6e900331f900
     health HEALTH_OK
     monmap e1: 1 mons at {node1=192.168.22.75:6789/0}
            election epoch 3, quorum 0 node1
     osdmap e25: 2 osds: 2 up, 2 in
            flags sortbitwise,require_jewel_osds
      pgmap v688: 112 pgs, 7 pools, 1588 bytes data, 171 objects
            18056 MB used, 16731 MB / 34788 MB avail
                 112 active+clean
 
2018-01-31 13:23:05.292270 mon.0 [INF] pgmap v688: 112 pgs: 112 active+clean; 1588 bytes data, 18056 MB used, 16731 MB / 34788 MB avail
```

检查集群状态

```
# ceph health
HEALTH_OK
```

### 添加元数据服务器

至少需要一个元数据服务器才能使用 CephFS，当前生产环境下的 Ceph 只能运行一个元数据服务器

```
# ceph-deploy mds create node1
 
[ceph_deploy.mds][DEBUG ] Deploying mds, cluster ceph hosts node1:node1
[node1][DEBUG ] connected to host: node1 
[node1][DEBUG ] detect platform information from remote host
[node1][DEBUG ] detect machine type
[ceph_deploy.mds][INFO ] Distro info: CentOS Linux 7.4.1708 Core
[ceph_deploy.mds][DEBUG ] remote host will use systemd
[ceph_deploy.mds][DEBUG ] deploying mds bootstrap to node1
[node1][DEBUG ] write cluster configuration to /etc/ceph/{cluster}.conf
[node1][DEBUG ] create path if it doesn't exist
[node1][INFO ] Running command: ceph --cluster ceph --name client.bootstrap-mds --keyring /var/lib/ceph/bootstrap-mds/ceph.keyring auth get-or-create mds.node1 osd allow rwx mds allow mon allow profile mds -o /var/lib/ceph/mds/ceph-node1/keyring
[node1][INFO ] Running command: systemctl enable ceph-mds@node1
[node1][WARNIN] Created symlink from /etc/systemd/system/ceph-mds.target.wants/ceph-mds@node1.service to /usr/lib/systemd/system/ceph-mds@.service.
[node1][INFO ] Running command: systemctl start ceph-mds@node1
[node1][INFO ] Running command: systemctl enable ceph.target
```

```
[root@node1 ~]# ps aux|grep ceph
ceph      1535  0.2  2.1 336520 21832 ?        Ssl  17:27   0:00 /usr/bin/ceph-mon -f --cluster ceph --id node1 --setuser ceph --setgroup ceph
ceph      2043  0.3  1.2 330504 12192 ?        Ssl  17:31   0:00 /usr/bin/ceph-mds -f --cluster ceph --id node1 --setuser ceph --setgroup ceph
```

### 添加RGW配置

```
# ceph-deploy rgw create node1
 
[ceph_deploy.rgw][DEBUG ] Deploying rgw, cluster ceph hosts node1:rgw.node1
[node1][DEBUG ] connected to host: node1 
[node1][DEBUG ] detect platform information from remote host
[node1][DEBUG ] detect machine type
[ceph_deploy.rgw][INFO ] Distro info: CentOS Linux 7.4.1708 Core
[ceph_deploy.rgw][DEBUG ] remote host will use systemd
[ceph_deploy.rgw][DEBUG ] deploying rgw bootstrap to node1
[node1][DEBUG ] write cluster configuration to /etc/ceph/{cluster}.conf
[node1][DEBUG ] create path recursively if it doesn't exist
[node1][INFO ] Running command: ceph --cluster ceph --name client.bootstrap-rgw --keyring /var/lib/ceph/bootstrap-rgw/ceph.keyring auth get-or-create client.rgw.node1 osd allow rwx mon allow rw -o /var/lib/ceph/radosgw/ceph-rgw.node1/keyring
[node1][INFO ] Running command: systemctl enable ceph-radosgw@rgw.node1
[node1][WARNIN] Created symlink from /etc/systemd/system/ceph-radosgw.target.wants/ceph-radosgw@rgw.node1.service to /usr/lib/systemd/system/ceph-radosgw@.service.
[node1][INFO ] Running command: systemctl start ceph-radosgw@rgw.node1
[node1][INFO ] Running command: systemctl enable ceph.target
[ceph_deploy.rgw][INFO ] The Ceph Object Gateway (RGW) is now running on host node1 and default port 7480
```

RGW 例程默认会监听 7480 端口，可以更改该节点 ceph.conf 内与 RGW 相关的配置，如下：

```
[client]
rgw frontends = civetweb port=80
```

```
[root@node1 ~]# ps aux|grep ceph
ceph      1535  0.2  2.2 338576 22824 ?        Ssl  17:27   0:00 /usr/bin/ceph-mon -f --cluster ceph --id node1 --setuser ceph --setgroup ceph
ceph      2043  0.0  1.2 330504 12192 ?        Ssl  17:31   0:00 /usr/bin/ceph-mds -f --cluster ceph --id node1 --setuser ceph --setgroup ceph
root      2145  1.3  1.1 1346308 11928 ?       Ssl  17:32   0:00 /usr/bin/radosgw -f --clusterceph --name client.rgw.node1 --setuser ceph --setgroup ceph
```

查看现在的monitor

```
ceph quorum_status --format json-pretty
{
    "election_epoch": 3,
    "quorum": [
        0
    ],
    "quorum_names": [
        "node1"
    ],
    "quorum_leader_name": "node1",
    "monmap": {
        "epoch": 1,
        "fsid": "c0c55799-7178-41aa-804e-6e900331f900",
        "modified": "2018-01-30 16:37:24.272258",
        "created": "2018-01-30 16:37:24.272258",
        "mons": [
            {
                "rank": 0,
                "name": "node1",
                "addr": "192.168.22.75:6789\/0"
            }
        ]
    }
}
```

```
# ceph osd tree
ID WEIGHT  TYPE NAME      UP/DOWN REWEIGHT PRIMARY-AFFINITY 
-1 0.03317 root default                                     
-2 0.01659     host node2                                   
 0 0.01659         osd.0       up  1.00000          1.00000 
-3 0.01659     host node3                                   
 1 0.01659         osd.1       up  1.00000          1.00000 
```

服务安装完毕，查看一下开机启动的服务

```
# systemctl list-unit-files|grep ceph|grep -v disabled
ceph-create-keys@.service                     static  
ceph-disk@.service                            static  
ceph-mds.target                               enabled 
ceph-mon.target                               enabled 
ceph-osd.target                               enabled 
ceph-radosgw.target                           enabled 
ceph.target                                   enabled
```

### **测试集群**

测试存取数据

```
# echo `date` > testfile
# rados mkpool testpool
successfully created pool testpool
# rados put object1 testfile --pool=testpool
# rados -p testpool ls
object1
# ceph osd map testpool object1
osdmap e20 pool 'testpool' (6) object 'object1' -> pg 6.bac5debc (6.4) -> up ([1,0], p1) acting ([1,0], p1)
```

删除本地的testfile，再获取这个文件

```
# rm -f testfile
# rados get object1 testfile --pool=testpool
# rados rm object1 --pool=testpool
# rados -p testpool ls
# rados rmpool testpool testpool --yes-i-really-really-mean-it
successfully deleted pool testpool
```



### **ceph块设备**

在虚拟机上运行 ceph-client 节点，但是不能在与 Ceph 存储集群（除非它们也用 VM ）相同的物理节点上执行下列步骤
新加一台主机，hostname为 ceph-client，我们在ceph-deploy主机部署安装，再在ceph-client主机操作

```
hostnamectl --static set-hostname ceph-client
```

并在/etc/hosts 添加ip和hostname对应关系
先安装ceph，再ceph-deploy 把 Ceph 配置文件和 ceph.client.admin.keyring 拷贝到 ceph-client

```
ceph-deploy install ceph-client
ceph-deploy admin ceph-client
```

```
[root@ceph-client ~]# ps aux|grep ceph
root      1581  0.0  0.0      0     0 ?        S<   17:26   0:00 [ceph-msgr]
root      1590  0.0  0.0      0     0 ?        S<   17:26   0:00 [ceph-watch-noti]
```

在ceph-client主机操作，这里只是测试，所以创建128M的块：

```
# rbd create clientrbd --size 128
# rbd map clientrbd --name client.admin
rbd: sysfs write failed
RBD image feature set mismatch. You can disable features unsupported by the kernel with "rbd feature disable".
In some cases useful info is found in syslog - try "dmesg | tail" or so.
rbd: map failed: (6) No such device or address
# dmesg -e|tail -n 3
[Jan31 13:39] libceph: mon0 192.168.22.75:6789 session established
[  +0.000763] libceph: client4154 fsid c0c55799-7178-41aa-804e-6e900331f900
[  +0.014563] rbd: image clientrbd: image uses unsupported features: 0x38
因为内核不支持新的特性，所以需要关闭，或者在ceph.conf增加rbd_default_features = 1
# rbd info 'clientrbd'
rbd image 'clientrbd':
	size 128 MB in 32 objects
	order 22 (4096 kB objects)
	block_name_prefix: rbd_data.103274b0dc51
	format: 2
	features: layering, exclusive-lock, object-map, fast-diff, deep-flatten
	flags:
```

layering: 支持分层
exclusive-lock: 支持独占锁
object-map: 支持对象映射(依赖 exclusive-lock)
fast-diff: 快速计算差异(依赖 object-map)
deep-flatten: 支持快照扁平化操作

```
# rbd feature disable clientrbd exclusive-lock, object-map, fast-diff, deep-flatten
# rbd map clientrbd --name client.admin
/dev/rbd0
格式化并挂载
# mkfs.ext4 -m0 /dev/rbd0
# mkdir /data
# mount /dev/rbd0 /data/
# ls /data/
lost+found
# df -h |grep data
/dev/rbd0                120M  1.6M  116M   2% /data
```

到这里，data目录就是刚创建的ceph块设备



### **文件系统**

查看状态

```
# ceph -s
```

已创建了元数据服务器，但如果你没有创建存储池和文件系统，它是不会变为活动状态的

```
ceph osd pool create cephfs_data <pg_num>
ceph osd pool create cephfs_metadata <pg_num>
ceph fs new <fs_name> cephfs_metadata cephfs_data
```

```
# ceph osd pool create cephfs_data 8
pool 'cephfs_data' created
[root@admin cluster]# ceph osd pool create cephfs_metadata 8
pool 'cephfs_metadata' created
[root@admin cluster]# ceph fs new bbottefs cephfs_metadata cephfs_data
new fs with metadata pool 8 and data pool 7
 
# awk 'NR==2{print $3}' ceph.client.admin.keyring > admin.secret
```

把 Ceph FS 挂载为**内核驱动**

```
# mkdir -p /data/kerneldata
# mount -t ceph 192.168.22.75:6789:/ /data/kerneldata -o name=admin,secretfile=admin.secret
# echo `date` > /data/kerneldata/file1
```

把 Ceph FS 挂载为**用户空间文件系统**（ FUSE ）

用户空间文件系统

```
# yum install ceph-fuse -y
# mkdir /data/fusedata
# ceph-fuse -m 192.168.22.75:6789 /data/fusedata/
ceph-fuse[20253]: starting ceph client
2018-01-31 16:48:30.749408 7f12b41fbec0 -1 init, newargv = 0x5654b03d6780 newargc=11
ceph-fuse[20253]: starting fuse
```

查看存储池

```
# rados lspools
rbd
.rgw.root
default.rgw.control
default.rgw.data.root
default.rgw.gc
default.rgw.log
cephfs_data
cephfs_metadata
default.rgw.users.uid
default.rgw.users.keys
default.rgw.users.swift
default.rgw.buckets.index
```



### **对象存储**

hadoop有一个web页面，ceph的web页面链接默认为monitor IP的7480端口
http://192.168.22.75:7480/
使用 REST 接口，首先需要为**S3接口**创建一个初始 Ceph 对象网关用户。然后，为 Swift 接口创建一个子用户。然后你需要验证创建的用户是否能够访问网关
ceph的网关api和亚马逊S3的api兼容

```
# radosgw-admin user create --uid="testuser" --display-name="Test User"
{
    "user_id": "testuser",
    "display_name": "Test User",
    "email": "",
    "suspended": 0,
    "max_buckets": 1000,
    "auid": 0,
    "subusers": [],
    "keys": [
        {
            "user": "testuser",
            "access_key": "F87KZIIW8G68J2GSS9FO",
            "secret_key": "4RktOVMgGlGeTQFKteUndGWFiRIr3N4EexVzD6iZ"
        }
    ],
    "swift_keys": [],
    "caps": [],
    "op_mask": "read, write, delete",
    "default_placement": "",
    "placement_tags": [],
    "bucket_quota": {
        "enabled": false,
        "max_size_kb": -1,
        "max_objects": -1
    },
    "user_quota": {
        "enabled": false,
        "max_size_kb": -1,
        "max_objects": -1
    },
    "temp_url_keys": []
}
```

新建一个 Swift 子用户。创建 Swift 用户包括两个步骤。第一步是**创建用户**。第二步是创建 secret key
为 S3 访问创建 RADOSGW 用户

```
# radosgw-admin subuser create --uid=testuser --subuser=testuser:swift --access=full
```

**新建秘钥**

```
# radosgw-admin key create --subuser=testuser:swift --key-type=swift --gen-secret
{
    "user_id": "testuser",
    "display_name": "Test User",
    "email": "",
    "suspended": 0,
    "max_buckets": 1000,
    "auid": 0,
    "subusers": [
        {
            "id": "testuser:swift",
            "permissions": "full-control"
        }
    ],
    "keys": [
        {
            "user": "testuser",
            "access_key": "F87KZIIW8G68J2GSS9FO",
            "secret_key": "4RktOVMgGlGeTQFKteUndGWFiRIr3N4EexVzD6iZ"
        }
    ],
    "swift_keys": [
        {
            "user": "testuser:swift",
            "secret_key": "ySkzpMPQPYmVrCl99eqv3x51fC3jFOBKVLqZcwJy"
        }
    ],
    "caps": [],
    "op_mask": "read, write, delete",
    "default_placement": "",
    "placement_tags": [],
    "bucket_quota": {
        "enabled": false,
        "max_size_kb": -1,
        "max_objects": -1
    },
    "user_quota": {
        "enabled": false,
        "max_size_kb": -1,
        "max_objects": -1
    },
    "temp_url_keys": []
}
```

验证 S3 访问，运行一个 Python 测试脚本。S3 访问测试脚本将连接 radosgw, 新建一个新的 bucket 并列出所有的 buckets。 aws_access_key_id 和 aws_secret_access_key 的值来自于命令``radosgw_admin`` 的返回值 access_key 和 secret_key

### ceph S3接口

```
# yum install python-boto
# cat s3_conn.py 
#!/usr/bin/env python
import boto
import boto.s3.connection
 
 
# radosgw-admin user create --uid="testuser" --display-name="Test User"
access_key = 'F87KZIIW8G68J2GSS9FO'
secret_key = '4RktOVMgGlGeTQFKteUndGWFiRIr3N4EexVzD6iZ'
conn = boto.connect_s3(
        aws_access_key_id = access_key,
        aws_secret_access_key = secret_key,
        host = '192.168.22.75', port = 7480, # change your host & port
        is_secure=False, calling_format = boto.s3.connection.OrdinaryCallingFormat(),
        )
 
# create bucket
bucket = conn.create_bucket('my-new-bucket')
for bucket in conn.get_all_buckets():
    print "{name}".format(
        name = bucket.name,
        created = bucket.creation_date,
        )
 
# get bucket file list
for key in bucket.list():
        print "{name}\t{size}\t{modified}".format(
                name = key.name,
                size = key.size,
                modified = key.last_modified,
                )
 
# create new file: hellt.txt
key = bucket.new_key('hello.txt')
key.set_contents_from_string('Hello World!')
 
# ACL
hello_key = bucket.get_key('hello.txt')
hello_key.set_canned_acl('public-read')
 
# get file
key = bucket.get_key('hello.txt')
key.get_contents_to_filename('/tmp/hello.txt')
 
# print file url
hello_key = bucket.get_key('hello.txt')
hello_url = hello_key.generate_url(0, query_auth=False, force_http=True)
print hello_url
 
# bucket.delete_key('hello.txt')
```

运行Python脚本

```
# python s3_conn.py 
my-new-bucket
http://192.168.22.75/my-new-bucket/hello.txt
 
# python s3_conn.py 
my-new-bucket
hello.txt 12 2018-01-31T10:57:18.773Z
http://192.168.22.75/my-new-bucket/hello.txt
```

我们通过url访问hello.txt，返回访问拒绝Connection refused，是因为网关用的默认端口7480，而不是80

```
# curl http://192.168.22.75:7480/my-new-bucket/hello.txt
Hello World!
# cat /tmp/hello.txt 
Hello World!
```

测试 **SWIFT** 访问
ceph swift接口测试

```
# yum install python-pip -y
# pip install --upgrade setuptools
# pip install --upgrade python-swiftclient
# swift -A http://192.168.22.75:7480/auth/1.0 -U testuser:swift -K "ySkzpMPQPYmVrCl99eqv3x51fC3jFOBKVLqZcwJy" list
my-new-bucket
 
# cat swift_conn.py 
#!/usr/bin/env python
import swiftclient
user = 'testuser:swift'
key = 'ySkzpMPQPYmVrCl99eqv3x51fC3jFOBKVLqZcwJy'
 
conn = swiftclient.Connection(
        user=user,
        key=key,
        authurl='http://192.168.22.75:7480/auth',
)
 
# create container
container_name = 'swift-container'
conn.put_container(container_name)
 
# create object
with open('/tmp/hello.txt', 'r') as hello_file:
    conn.put_object(container_name, 'world.txt',
                    contents=hello_file.read(),
                    content_type='text/plain')
 
for container in conn.get_account()[1]:
    print container['name']
 
for data in conn.get_container(container_name)[1]:
    print '{0}\t{1}\t{2}'.format(data['name'], data['bytes'], data['last_modified'])
 
obj_tuple = conn.get_object(container_name, 'world.txt')
with open('/tmp/world.txt', 'w') as my_hello:
        my_hello.write(obj_tuple[1])
 
conn.delete_object(container_name, 'world.txt')
 
conn.delete_container(container_name)
```

测试swift接口

```
# python swift_conn.py 
my-new-bucket
swift-container
world.txt	12	2018-01-31T11:19:55.393Z
[root@admin cluster]# cat /tmp/world.txt 
Hello World!
 
res, err = red:eval(
"local res, err = redis.call('incr',KEYS[1]) 
  if res == 1 
  then local resexpire, err = redis.call('expire',KEYS[1],KEYS[2]) 
  end 
  return (res)"
  ,2,uriKey,1
)
```

ceph基础应用如上，下一篇介绍作为kubernetes的存储使用

2018年02月08日 于 [linux工匠](http://www.bbotte.com/) 发表