# 一分钟简单了解docker和kubernetes



先放一组简单的对应关系，下面分类并没有严格划分，重量级是指os级别的虚拟化，轻量级是指进程虚拟化

|            | 重量级                                | 轻量级              |
| ---------- | ---------------------------------- | ---------------- |
| 服务及包含服务的系统 | Xen、kvm、VMware                     | docker           |
| 调度服务平台     | OpenStack、OpenShift、VMware vSphere | kubernetes、swarm |

### namespace和cgroup

Xen、kvm、qemu虚拟机能做到环境隔离，资源限制，对于linux内核来说也实现了这2个功能：
1.linux内核的资源隔离:**namespace**

（man namespace查看文档）仅是一个系统调用，轻量级进程虚拟化，隔离进程，使期进程与其他进程有不同的系统视图。可以隔离的资源有：挂载磁盘、进程pid、网络、ipc(进程间通信)、hostname、user

2.linux内核对资源限制:**cgroup**

cgroup对cpu/memory/network/disk等资源限制，systemd默认挂载在/sys/fs/cgroup 目录

cgroup是一个资源管理解决方案，提供通用的流程分组框架。cgroup使用虚拟文件系统vfs，并不是持久化存储。所有cgroups操作都是通过文件系统操作（创建/删除目录，读取/写入其中的文件，安装/挂载选项）来执行的。就是说cgroup需要一个子系统，而子系统用到vfs，所以首先要挂载，挂载目录可以是随便一个，systemd默认在/sys/fs/cgroup目录，查看系统使用的cgroup：

```
cat /proc/mounts | grep cgroup
```

有了namespace和cgroup催化了容器技术的发展，于是生成了linux服务器下原生的lxc

### lxc

再说说lxc，**lxc**(Linux Container)是一种内核虚拟化技术，可以提供轻量级的虚拟化，以便隔离进程和资源
用namespace隔离资源，用cgroup限制资源使用(yum install lxc 安装)。

lxc是一种操作系统层虚拟化（Operating system–level virtualization）技术，为Linux内核容器功能的一个用户空间接口。它将应用软件系统打包成一个软件容器（Container），内含应用软件本身的代码，以及所需要的操作系统核心和库。透过统一的名字空间和共享API来分配不同软件容器的可用硬件资源，创造出应用程序的独立沙箱运行环境，使得Linux用户可以容易的创建和管理系统或应用容器。

在Linux内核中，提供了cgroups功能，来达成资源的区隔化。它同时也提供了名称空间区隔化的功能，使应用程序看到的操作系统环境被区隔成独立区间，包括行程树，网络，用户id，以及挂载的文件系统。但是cgroups并不一定需要引导任何虚拟机。

LXC利用cgroups与名称空间的功能，提供应用软件一个独立的操作系统环境。LXC不需要Hypervisor这个软件层，软件容器（Container）本身极为轻量化，提升了创建虚拟机的速度。软件Docker被用来管理LXC的环境。（以上3截内容来自维基百科）

lxc就是一个虚拟机，直接运行在内核上，功能是全的，不过这个用起来有些简陋，把lxc这个产品包装一下，变为更易用，方便管理的服务，就诞生了—-**docker**

### docker

docker简单说分2部分，由docker控制镜像的创建、运行、销毁
1.docker运行控制
2.docker镜像

docker运行控制即服务的create、execute、start、kill、stop、destroy、monitor
docker镜像是一个带有服务的完整系统，由Dockerfile文件中指令生成，分层(步骤)生成的运行指定命令的操作系统。一般来说一个docker镜像只运行一个服务

docker完成了控制一套完整系统(docker 镜像)的运行，和Xen、kvm对虚拟机的管理一样

Docker现在已经开发了他们自己的直接使用核心namespaces和cgroup的工具：libcontainer。 分层容器 Docker最开始是基于LXC对Aufs的支持来建立分层容器，因为Aufs可能无法被合并到核心中，所以现在对Brtfs、设备映射和覆盖也添加支持， Docker容器技术是由基底镜像构成，当提交变成Docker镜像的时候会再加上一个分层面板。当运行一个镜像的时候，它的复本就作为容器被启动了，在提交之前，它的任何数据都只是暂时的。每一个提交都是一个独立的镜像，所以可以从镜像开始

LXC是一种容器技术，它为您提供了轻量级的Linux容器，Docker是一个基于容器的单一应用程序虚拟化引擎。

再来说对虚拟机的调度，OpenStack就是对虚拟机调度平台，只是偏重量级
而**kubernetes**服务编排系统更轻量级、灵活、简单

### kubernetes

kubernetes分为4部分：
1.api(etcd数据库)
2.任务调度
3.资源调度
4.客户端kubelet



**API**: k8s集群所有信息都是存在etcd KV数据库中，用来存储所有 Kubernetes 的集群状态的，它除了具备状态存储的功能，还有事件监听和订阅、Leader 选举的功能，所谓事件监听和订阅，各个其他组件通信，都并不是互相调用 API 来完成的，而是把状态写入 etcd（相当于写入一个消息），其他组件通过监听 etcd 的状态的的变化（相当于订阅消息），然后做后续的处理，再一次把更新的数据写入 etcd，由api server RESTFul 接口接收、发送相应请求，读取、写入etcd

**任务调度**：Controller Manager, docker的生命周期管理，服务发现，路由，扩展，垃圾回收等操作, 比如 Deployment 、Deamon Set 或者 Job，每一个任务请求发送给Kubernetes 之后，都是由 Controller Manager 来处理的

**资源调度**：根据资源可用性调度服务，限制某节点允许或禁止运行等，把pod调用到适合的node节点

**kubelet**客户端：节点的守护进程，监听 etcd 中的 Pod 信息，定期向主节点汇报资源使用情况，确保运行的服务是任务调度的期望状态

k8s集群并没有提供原生的dns、存储、网络、日志收集、监控报警等功能，是通过外部接口实现，所以在k8s集群安装完成后，再安装附件add-on

从linux内核namespace和cgroup功能衍生出容器这个产品，并由谷歌做出kubernetes平台负责对容器的调度，简单的关系就是这样