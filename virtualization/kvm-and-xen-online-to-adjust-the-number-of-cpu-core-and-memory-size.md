---
layout: default
---

# kvm和Xen主机在线调整cpu核心数和内存大小

1. kvm的cpu和内存调整
2. kvm调整cpu核数
3. kvm调整内存使用
4. Xen主机的cpu核数和内存大小设置

### 说明

因为线上经常会遇到资源分配不均衡，我认为使用虚拟化主机主要原因：一是资源隔离，每台机负载一块任务，多台虚拟主机在资源有限情况下可以做到高可用； 二是尽可能的利用服务器的硬件资源，避免某些物理服务器异常繁忙或没有负载。 我一般的把服务器刚开始设置较低的配置，根据服务的运行负载情况调整cpu & mem

[kvm的安装配置](http://bbotte.com/kvm-xen/virtualization-of-kvm-configuration-applications/)应用  &  [xen主机的安装配置应用](http://bbotte.com/kvm-xen/virtualization-of-xen-project-configuration-applications/)  & [kvm&Xen主机在线增加磁盘空间](http://bbotte.com/kvm-xen/kvm-and-xen-host-online-increase-disk-space/)

### **kvm的cpu和内存调整**

kvm我们用virsh控制台

```
关机状态下设置最大cpu颗数和最大内存使用量(此步骤必须)：
 
# virsh list --all 
Id    Name         State
-------------------------------------------------
-     bbotte       shut off 
    
# virsh setvcpus bbotte  --maximum 4 --config   #最大cpu核数为4
# virsh setmaxmem bbotte  1048576 --config      #最大内存为1G
```

```
# virsh dominfo bbotte       #现在主机配置,2核，512M内存
Id:             2
Name:           bbotte
UUID:           bd22f444-ee7f-7f00-3d1b-1bb0d0857e43
OS Type:        hvm
State:          running
CPU(s):         2
CPU time:       152.3s
Max memory:     1048576 KiB           #上面设置的最大可用内存
Used memory:    524288 KiB            #现在使用的内存大小
Persistent:     yes
Autostart:      disable
Managed save:   no
Security model: none
Security DOI:   0
   
# ps -C qemu-kvm -o rss,cmd
  RSS CMD
388736 /usr/libexec/qemu-kvm -name bbotte -S -M rhel6.6.0 -enable-kvm -m 512 -realtime mlock
```

### kvm调整cpu核数

```
virsh setvcpus [domain-name, domain-id or domain-uuid] [count]
从2颗cpu增至4颗
# virsh setvcpus bbotte 4
guest主机里面命令行会自动弹出log：
# CPU 2 got hotplugged
Booting Node 0 Processor 2 APIC 0x2
CPU 3 got hotplugged
kvm-clock: cpu 2, msr 0:23167c1, secondary cpu clock
Disabled fast string operations
kvm-stealtime: cpu 2, msr 230e880
Will online and init hotplugged CPU: 2
Booting Node 0 Processor 3 APIC 0x3
kvm-clock: cpu 3, msr 0:23967c1, secondary cpu clock
Disabled fast string operations
kvm-stealtime: cpu 3, msr 238e880
Will online and init hotplugged CPU: 3
```

### kvm调整内存使用

```
virsh setmem [domain-id or domain-name]  [count]
现在的内存为512M，调整为800M的话：
# virsh setmem bbotte 819200 --config --live
# virsh setmem bbotte 800M  或者用此命令更简洁
 
查看现在主机配置
# virsh dominfo bbotte
Id:             2
Name:           bbotte
UUID:           bd22f444-ee7f-7f00-3d1b-1bb0d0857e43
OS Type:        hvm
State:          running
CPU(s):         4
CPU time:       163.9s
Max memory:     1048576 KiB
Used memory:    819200 KiB
Persistent:     yes
Autostart:      disable
Managed save:   no
Security model: none
Security DOI:   0
```

当然cpu核数和内存大小可用降低，往小调整的时候需要小心

### **Xen主机的cpu核数和内存大小设置**

控制xen主机我们用自定义的配置文件，和设置kvm主机一样，需要事先定义一个变更大小的范围

```
# vim bbotte
 
name = "bbotte"
vcpus = 1                  #开机的cpu核数
maxvcpus = 10              #可用调整最大的cpu核数
memory = 2048              #开机后的内存大小
maxmem = 20480             #可以调整的内存大小
disk = [ "file:/data/bbotte.qcow2,xvda,w", ]
vif = [ "bridge=br0" ]
on_reboot = "restart"
on_crash = "destroy"
```

上述xen虚拟主机，默认配置为1核，2G，可以调整最大的配置为：10核，20G

修改cpu：
xm vcpu-list                                 #查看cpu的使用
xm vcpu-set bbotte 6                   #修改bbotte的cpu颗数为6

修改内存：
xm mem-set bbotte 16384          #调整bbotte的内存为16G
xm mem-set bbotte 20480          #调整bbotte的内存为20G

xm top                                        #查看当前各主机的状态

虚拟主机改变配置就是这么方便 ^_^

2016年03月28日 于 [linux工匠](https://bbotte.github.io/) 发表



































