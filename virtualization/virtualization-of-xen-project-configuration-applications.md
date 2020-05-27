---
layout: default
---

# 虚拟化之Xen配置应用

1. Xen说明
2. Xen安装
3. 配置网卡
4. 安装一台虚拟机
5. 启动此虚拟机
6. 控制台常用的命令

### Xen说明

本文讲述Xen服务在CentOS平台安装、dom0虚拟主机安装、控制台管理等基础功能的使用

![虚拟化之Xen配置应用 - 第1张](http://bbotte.com/wp-content/uploads/2016/03/xen-logo.png)

Xen Project是领先的开源虚拟化平台，已在全球最大的云服务平台应用。亚马逊，阿里云，Rackspace公共云，Verizon云平台和许多托管服务都使用Xen项目。另外，它被集成到多个云解决方案项目，如OpenStack。Xen官网<http://www.xenproject.org/>

### **Xen安装**

OS：CentOS-6.7-x86_64-minimal.iso

默认已经开启了cpu的虚拟化(参考[虚拟化之KVM配置应用](http://bbotte.com/kvm-xen/virtualization-of-kvm-configuration-applications/)中**开启虚拟化**)，系统已经关闭selinux（setenforce 0;sed -i ‘s/SELINUX=enforcing/SELINUX=disabled/g’ /etc/selinux/config）

```
# yum install gcc gcc-c++ vim wget lrzsz ntpdate sysstat dstat wget -y
# sed -i 's#net.ipv4.ip_forward = 0#net.ipv4.ip_forward = 1#' /etc/sysctl.conf 
# sysctl -p
 
# yum install centos-release-xen -y
安装了下面两个包
1，centos-release-virt-common
2，centos-release-xen
# yum install xen
===================================================================================================
 Package                   Arch         Version                        Repository             Size
===================================================================================================
Installing:
 xen                       x86_64       4.4.3-12.el6                   centos-virt-xen       1.0 M
Installing for dependencies:
 SDL                       x86_64       1.2.14-7.el6_7.1               updates               193 k
 glusterfs                 x86_64       3.6.0.55-1.el6                 updates               1.3 M
 glusterfs-api             x86_64       3.6.0.55-1.el6                 updates                62 k
 glusterfs-libs            x86_64       3.6.0.55-1.el6                 updates               272 k
 gnutls                    x86_64       2.8.5-19.el6_7                 updates               347 k
 kernel                    x86_64       3.18.25-19.el6                 centos-virt-xen        36 M
 libX11                    x86_64       1.6.0-6.el6                    base                  586 k
 libX11-common             noarch       1.6.0-6.el6                    base                  192 k
 libXau                    x86_64       1.0.6-4.el6                    base                   24 k
 libXdamage                x86_64       1.1.3-4.el6                    base                   18 k
 libXext                   x86_64       1.3.2-2.1.el6                  base                   35 k
 libXfixes                 x86_64       5.0.1-2.1.el6                  base                   17 k
 libXxf86vm                x86_64       1.1.3-2.1.el6                  base                   16 k
 libpng                    x86_64       2:1.2.49-2.el6_7               updates               182 k
 libusb1                   x86_64       1.0.9-0.6.rc1.el6              base                   80 k
 libxcb                    x86_64       1.9.1-3.el6                    base                  110 k
 libxslt                   x86_64       1.1.26-2.el6_3.1               base                  452 k
 mesa-dri-drivers          x86_64       10.4.3-1.el6                   base                   14 M
 mesa-dri-filesystem       x86_64       10.4.3-1.el6                   base                   16 k
 mesa-dri1-drivers         x86_64       7.11-8.el6                     base                  3.8 M
 mesa-libGL                x86_64       10.4.3-1.el6                   base                  146 k
 mesa-private-llvm         x86_64       3.4-3.el6                      base                  5.6 M
 pciutils                  x86_64       3.1.10-4.el6                   base                   85 k
 pixman                    x86_64       0.32.4-4.el6                   base                  243 k
 python-lxml               x86_64       2.2.3-1.1.el6                  base                  2.0 M
 qemu-img                  x86_64       2:0.12.1.2-2.479.el6_7.4       updates               831 k
 usbredir                  x86_64       0.5.1-2.el6                    base                   40 k
 xen-hypervisor            x86_64       4.4.3-12.el6                   centos-virt-xen       4.7 M
 xen-libs                  x86_64       4.4.3-12.el6                   centos-virt-xen       428 k
 xen-licenses              x86_64       4.4.3-12.el6                   centos-virt-xen        84 k
 xen-runtime               x86_64       4.4.3-12.el6                   centos-virt-xen       9.9 M
 yajl                      x86_64       1.0.7-3.el6                    base                   27 k
Updating for dependencies:
 kernel-firmware           noarch       3.18.25-19.el6                 centos-virt-xen       6.4 M
 
Transaction Summary
===================================================================================================
Install      33 Package(s)
Upgrade       1 Package(s)
 
# /usr/bin/grub-bootxen.sh
Updating grub config
# vim /boot/grub/grub.conf
#boot=/dev/sda
default=0
timeout=5
splashimage=(hd0,0)/grub/splash.xpm.gz
hiddenmenu
title CentOS (3.18.25-19.el6.x86_64)
        root (hd0,0)
        kernel /xen.gz dom0_mem=1024M,max:1024M cpuinfo com1=115200,8n1 console=com1,tty loglvl=all guest_loglvl=all
        module /vmlinuz-3.18.25-19.el6.x86_64 ro root=/dev/mapper/VolGroup-lv_root rd_NO_LUKS LANG=en_US.UTF-8 rd_NO_MD rd_LVM_LV=VolGroup/lv_swap SYSFONT=latarcyrheb-sun16 crashkernel=auto rd_LVM_LV=VolGroup/lv_root  KEYBOARDTYPE=pc KEYTABLE=us rd_NO_DM rhgb quiet
        module /initramfs-3.18.25-19.el6.x86_64.img   #添加了此行#
title CentOS (2.6.32-573.18.1.el6.x86_64)
        root (hd0,0)
        kernel /vmlinuz-2.6.32-573.18.1.el6.x86_64 ro root=/dev/mapper/VolGroup-lv_root rd_NO_LUKS LANG=en_US.UTF-8 rd_NO_MD rd_LVM_LV=VolGroup/lv_swap SYSFONT=latarcyrheb-sun16 crashkernel=auto rd_LVM_LV=VolGroup/lv_root  KEYBOARDTYPE=pc KEYTABLE=us rd_NO_DM rhgb quiet
        initrd /initramfs-2.6.32-573.18.1.el6.x86_64.img
title CentOS 6 (2.6.32-573.el6.x86_64)
        root (hd0,0)
        kernel /vmlinuz-2.6.32-573.el6.x86_64 ro root=/dev/mapper/VolGroup-lv_root rd_NO_LUKS LANG=en_US.UTF-8 rd_NO_MD rd_LVM_LV=VolGroup/lv_swap SYSFONT=latarcyrheb-sun16 crashkernel=auto rd_LVM_LV=VolGroup/lv_root  KEYBOARDTYPE=pc KEYTABLE=us rd_NO_DM rhgb quiet
        initrd /initramfs-2.6.32-573.el6.x86_64.img
 
# yum install libvirt python-virtinst libvirt-daemon-xen virt-manager virt-viewer -y
# chkconfig xend on
# shutdown -r now
```

查看安装好的Xen

```
[root@localhost ~]# xm list
WARNING: xend/xm is deprecated.
Name                                        ID   Mem VCPUs      State   Time(s)
Domain-0                                     0  1024     4     r-----     11.6
[root@localhost ~]# xl info
host                   : localhost.localdomain
release                : 3.18.25-19.el6.x86_64
version                : #1 SMP Wed Mar 16 19:11:01 UTC 2016
machine                : x86_64
nr_cpus                : 4
max_cpu_id             : 63
nr_nodes               : 1
cores_per_socket       : 1
threads_per_core       : 1
cpu_mhz                : 3191
hw_caps                : 0fabfbff:2c100800:00000000:00003f00:f6fa3223:00000000:00000001:00000281
virt_caps              : hvm
total_memory           : 1663
free_memory            : 617
sharing_freed_memory   : 0
sharing_used_memory    : 0
outstanding_claims     : 0
free_cpus              : 0
xen_major              : 4
xen_minor              : 4
xen_extra              : .3-12.el6
xen_version            : 4.4.3-12.el6
xen_caps               : xen-3.0-x86_64 xen-3.0-x86_32p hvm-3.0-x86_32 hvm-3.0-x86_32p hvm-3.0-x86_64 
xen_scheduler          : credit
xen_pagesize           : 4096
platform_params        : virt_start=0xffff800000000000
xen_changeset          : Wed Feb 17 12:38:38 2016 +0000 git:8978853-dirty
xen_commandline        : dom0_mem=1024M,max:1024M cpuinfo com1=115200,8n1 console=com1,tty loglvl=all guest_loglvl=all
cc_compiler            : gcc (GCC) 4.4.7 20120313 (Red Hat 4.4.7-16)
cc_compile_by          : mockbuild
cc_compile_domain      : centos.org
cc_compile_date        : Wed Feb 17 13:09:36 UTC 2016
xend_config_format     : 4
```

另：VMware虚拟机需要更改安装虚拟机文件夹的CentOS 64-bit.vmx文件， vcpu.hotadd = “TRUE” 改为vcpu.hotadd = “FALSE”

### **配置网卡**

```
# cp /etc/sysconfig/network-scripts/ifcfg-eth0 /etc/sysconfig/network-scripts/ifcfg-br0
# vim /etc/sysconfig/network-scripts/ifcfg-br0
DEVICE=br0
TYPE=Bridge
ONBOOT=yes
NM_CONTROLLED=yes
BOOTPROTO=none
IPADDR=192.168.71.45
PREFIX=24
DEFROUTE=yes
PEERDNS=yes
PEERROUTES=yes
IPV4_FAILURE_FATAL=yes
IPV6INIT=no
NAME="System br0"
 
# vim /etc/sysconfig/network-scripts/ifcfg-eth0 
DEVICE=eth0
TYPE=Ethernet
ONBOOT=yes
NM_CONTROLLED=yes
BOOTPROTO=none
BRIDGE=br0
DEFROUTE=yes
PEERDNS=yes
PEERROUTES=yes
IPV4_FAILURE_FATAL=yes
IPV6INIT=no
NAME="System eth0"
 
 
# service network restart
# brctl show
bridge name	bridge id		STP enabled	interfaces
br0		8000.000c298abf8f	no		eth0
 
# service libvirtd start
 
# service libvirtd status
libvirtd (pid  1908) is running...
# chkconfig libvirtd on
```

### **安装一台虚拟机**

下面是用自己设置http服务的系统源来做的，参考[虚拟化之KVM配置应用](http://bbotte.com/kvm-xen/virtualization-of-kvm-configuration-applications/)中**配置安装虚拟机的源**

virt-install安装guest：

```
# virt-install -n bbotte_1 -r 512 --vcpus=2 --disk /data/bbotte_1.img,size=10 --nographics -p -l "http://192.168.71.45" -w bridge:br0 --extra-args="text console=com1 utf8 console=hvc0"
 
name bbotte_1
内存 512M
cpu 2颗
磁盘文件 /data/bbotte_1.img
磁盘大小 10G
```

也可以选择交互式安装 virt-install –prompt

```
# virt-install --prompt
Would you like a fully virtualized guest (yes or no)? This will allow you to run unmodified operating systems. 
yes
What is the name of your virtual machine? 
bbotte_1
How much RAM should be allocated (in megabytes)? 
512
What would you like to use as the disk (file path)? 
/data/bbotte_1.img
How large would you like the disk (/data/bbotte_1.img) to be (in gigabytes)? 
10
What is the install CD-ROM/ISO or URL? 
http://192.168.71.45/               #或者/data/CentOS-6.7-x86_64-minimal.iso 
 
Starting install...
Retrieving file .treeinfo...                                      |  676 B     00:00 ... 
Retrieving file vmlinuz...                                        | 8.1 MB     00:00 ... 
Retrieving file initrd.img...                                     |  69 MB     00:00 ... 
Creating storage file devops2u_1.img                              |  10 GB     00:00     
Creating domain...                                                |    0 B     00:01     
Connected to domain devops2u_1
Escape character is ^]
```

而我一般是新建配置文件管理虚拟机，建议大家也这样操作：

```
# cd /data
# qemu-img create -f qcow2  -o size=6G,preallocation=metadata /data/centos1.qcow2
Formatting '/data/centos1.qcow2', fmt=qcow2 size=6374182400 encryption=off cluster_size=65536 preallocation='metadata'
 
# vim bbotte_1
kernel = "/var/www/centos/cdrom/images/pxeboot/vmlinuz"        #没有vmlinuz的话就从iso里面找一个
ramdisk = "/var/www/centos/cdrom/images/pxeboot/initrd.img"
name = "bbotte_1"
memory = "512"
disk = [ "file:/data/bbotte.qcow2,xvda,w", ]            #指定磁盘文件，img格式的可以事先不用设置，会自动生成，qcow2需要手动生成，可以指定多块磁盘文件
#disk = [ "file:/data/bbotte.img,xvda,w", "file:/data/centos2.img,xvdb,w" ]  #此行注释是举个例子给大家看
vif = [ "bridge=br0" ]                                   #多块网卡就在后面添加配置
vcpus = 2
on_reboot = "destroy"                                    #首次安装系统会重启，如果是restart，则又进入安装系统界面，所以第一次写destroy以停止
on_crash = "destroy" 
 
 
 
# xm create bbotte_1 -c
WARNING: xend/xm is deprecated.
Using config file "./bbotte_1".
Started domain bbotte_1 (id=1)
                                Initializing cgroup subsys cpuset
Initializing cgroup subsys cpu
...
...
                    ┌────────┤ Choose a Language ├────────┐
                    │                                     │
                    │ What language would you like to use │
                    │ during the installation process?    │
                    │                                     │
                    │      Catalan                ↑       │
                    │      Chinese(Simplified)    ▒       │
                    │      Chinese(Traditional)   ▮       │
                    │      Croatian               ▒       │
                    │      Czech                  ▒       │
                    │      Danish                 ▒       │
                    │      Dutch                  ▒       │
                    │      English                ↓       │
                    │               ┌────┐                │
                    │               │ OK │                │
                    │               └────┘                │
                    └─────────────────────────────────────┘

```

```
Welcome to CentOS for x86_64       
                    
                        ┌───┤ Installation Method ├───┐
                        │                             │
                        │ What type of media contains │
                        │ the installation image?     │
                        │                             │
                        │        Local CD/DVD         │
                        │        Hard drive           │
                        │        NFS directory        │
                        │        URL                  │
                        │   ┌────┐       ┌──────┐     │
                        │   │ OK │       │ Back │     │
                        │   └────┘       └──────┘     │
                        └─────────────────────────────┘
```

选择URL安装，下一步设置一个ip地址

```
Welcome to CentOS for x86_64
 
                    
                 ┌────────────┤ Configure TCP/IP ├────────────┐
                 │                                            │
                 │ [*] Enable IPv4 support                    │
                 │        ( ) Dynamic IP configuration (DHCP) │
                 │        (*) Manual configuration            │
                 │                                            │
                 │ [ ] Enable IPv6 support                    │
                 │        (*) Automatic                       │
                 │        ( ) Automatic, DHCP only            │
                 │        ( ) Manual configuration            │
                 │                                            │
                 │        ┌────┐              ┌──────┐        │
                 │        │ OK │              │ Back │        │
                 │        └────┘              └──────┘        │
                 └────────────────────────────────────────────┘
```

```
Welcome to CentOS for x86_64
 
                    
       ┌────────────────┤ Manual TCP/IP Configuration ├─────────────────┐
       │                                                                │
       │ Enter the IPv4 and/or the IPv6 address and prefix (address /   │
       │ prefix).  For IPv4, the dotted-quad netmask or the CIDR-style  │
       │ prefix are acceptable. The gateway and name server fields must │
       │ be valid IPv4 or IPv6 addresses.                               │
       │                                                                │
       │ IPv4 address: 192.168.71.99___ / 24______________              │
       │ Gateway:      _________________________________________        │
       │ Name Server:  _________________________________________        │
       │                                                                │
       │             ┌────┐                        ┌──────┐             │
       │             │ OK │                        │ Back │             │
       │             └────┘                        └──────┘             │
       └────────────────────────────────────────────────────────────────┘
```

这一步是选择安装url的源，因为配置过，写自己设置的（kvm那一篇有写安装http，设置源），如果没有设置，那么选择阿里云、搜狐、网易源也可以

```
Welcome to CentOS for x86_64
 
        ┌────────────────────────┤ URL Setup ├─────────────────────────┐
        │                                                              │
        │          Please enter the URL containing the CentOS          │
        │          installation image on your server.                  │
        │                                                              │
        │ http://192.168.71.45________________________________________ │
        │                                                              │
        │ [ ] Enable HTTP proxy                                        │
        │                                                              │
        │ Proxy URL        ___________________________________         │
        │ Username         _______________                             │
        │                                                              │
        │ Password         _______________                             │
        │                                                              │
        │            ┌────┐                       ┌──────┐             │
        │            │ OK │                       │ Back │             │
        │            └────┘                       └──────┘             │
        └──────────────────────────────────────────────────────────────┘

```

```
Welcome to CentOS for x86_64
 
               ┌──────────────────┤ CentOS ├───────────────────┐
               │                                               │
               │ Welcome to CentOS!                            │
               │                    ┌────┐                     │
               │                    │ OK │                     │
               │                    └────┘                     │
               └───────────────────────────────────────────────┘
```

下面一步是初始化磁盘，就是上面我们定义的devops2u_1.qcow2文件，要选择“ Re-initialize all”

```
Welcome to CentOS for x86_64
 ┌────────────────────────────────┤ Warning ├─────────────────────────────────┐
 │                                                                            │
 │         Error processing drive:                                 ↑          │
 │                                                                 ▮          │
 │         xen-vbd-51712                                           ▒          │
 │         6145MB                                                  ▒          │
 │         Xen Virtual Block Device                                ▒          │
 │                                                                 ▒          │
 │         This device may need to be reinitialized.               ▒          │
 │                                                                 ▒          │
 │         REINITIALIZING WILL CAUSE ALL DATA TO BE LOST!          ▒          │
 │                                                                 ▒          │
 │         This action may also be applied to all other disks      ▒          │
 │         needing reinitialization.                               ↓          │
 │                                                                            │
 │  ┌────────┐   ┌────────────┐   ┌───────────────┐   ┌───────────────────┐   │
 │  │ Ignore │   │ Ignore all │   │ Re-initialize │   │ Re-initialize all │   │
 │  └────────┘   └────────────┘   └───────────────┘   └───────────────────┘   │
 └────────────────────────────────────────────────────────────────────────────┘
```

继续下一步，到选择时区，设置密码，

```
Welcome to CentOS for x86_64
 
                    ┌───────┤ Time Zone Selection ├───────┐
                    │                                     │
                    │ In which time zone are you located? │
                    │                                     │
                    │ [ ] System clock uses UTC           │
                    │                                     │
                    │  Asia/Shanghai                   ↑  │
                    │  Asia/Singapore                  ▒  │
                    │  Asia/Srednekolymsk              ▮  │
                    │  Asia/Taipei                     ▒  │
                    │  Asia/Tashkent                   ↓  │
                    │                                     │
                    │      ┌────┐          ┌──────┐       │
                    │      │ OK │          │ Back │       │
                    │      └────┘          └──────┘       │
                    └─────────────────────────────────────┘
```

```
Welcome to CentOS for x86_64
 
       ┌─────────────────────┤ Partitioning Type ├─────────────────────┐
       │                                                               │
       │ Installation requires partitioning of your hard drive.  The   │
       │ default layout is suitable for most users.  Select what space │
       │ to use and which drives to use as the install target.         │
       │                                                               │
       │                 Use entire drive                              │  #使用全部硬盘
       │                 Replace existing Linux system                 │
       │                 Use free space                                │
       │                                                               │
       │   Which drive(s) do you want to use for this installation?    │
       │      [*]   xvda     6145 MB (Xen Virtual Block Devic) ↑       │
       │                                                       ▮       │
       │                                                               │
       │                      ┌────┐   ┌──────┐                        │
       │                      │ OK │   │ Back │                        │
       │                      └────┘   └──────┘                        │
       └───────────────────────────────────────────────────────────────┘
```

格式化之后，就开始安装了，

```
Welcome to CentOS for x86_64
       
     ┌─────────────────────┤ Package Installation ├──────────────────────┐
     │                                                                   │
     │                                 6%                                │
     │                                                                   │
     │                   Packages completed: 7 of 205                    │
     │                                                                   │
     │ Installing glibc-common-2.12-1.166.el6.x86_64 (107 MB)            │
     │ Common binaries and locale data for glibc                         │
     │                                                                   │
     └───────────────────────────────────────────────────────────────────┘
```

安装过程中也可以选择使用vnc，这样图形化界面更方便

安装完成之后需要修改一下配置文件

```
# vim bbotte_1 
name = "bbotte_1"
memory = "512"
disk = [ "file:/data/bbotte.qcow2,xvda,w", ]
vif = [ "bridge=br0" ]
vcpus = 2
on_reboot = "restart"
on_crash = "destroy"
```

### 启动此虚拟机

\# xm create bbotte_1 -c

设置ip，同步时间，初始化系统

登录后，exit退出登录，Ctrl + ] 回退到控制台命令行

```
# xm list
WARNING: xend/xm is deprecated.
Name                                        ID   Mem VCPUs      State   Time(s)
Domain-0                                     0  1024     4     r-----     64.8
bbotte_1                                   2   512     2     -b----      9.2
```

### 控制台常用的命令

```
xm list                   #查看已有guest
xm create <config_file>   #启动配置文件的虚拟机
xm console <Domain_name>  #连接虚拟机
xm destroy centos1        #拔电源关机
xm shutdown centos1       #关机
xm start centos1          #启动
```

xl: Xen Project management tool, based on LibXenlight  xl是xm的升级版，许多命令都兼容

xm top  查看主机和各个虚拟机的资源利用情况

- 2016年03月23日 于 [linux工匠](https://bbotte.github.io/) 发表









