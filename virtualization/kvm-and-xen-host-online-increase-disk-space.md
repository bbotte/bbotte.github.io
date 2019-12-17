---
layout: default
---

# kvm和Xen主机在线增加磁盘空间

1. Xen guest主机扩充磁盘空间
2. 扩展lvm
3. 对lvm格式磁盘增加空间
4. KVM的guest热扩充磁盘
5. 重启方式增大磁盘空间

上一篇文章写了[kvm&Xen主机在线调整cpu核心数和内存大小](http://bbotte.com/kvm-xen/kvm-and-xen-online-to-adjust-the-number-of-cpu-core-and-memory-size/)，现在说一下扩充KVM和Xen虚拟主机的磁盘空间，利用lvm磁盘格式，增加磁盘的大小。[kvm的安装配置](http://bbotte.com/kvm-xen/virtualization-of-kvm-configuration-applications/)应用   [xen主机的安装配置应用](http://bbotte.com/kvm-xen/virtualization-of-xen-project-configuration-applications/)

### **Xen guest主机扩充磁盘空间**

说一下思路：在kvm或xen主机新建磁盘文件，用virsh attach-disk 命令把此文件附加到正在运行的虚拟主机。在虚拟主机内分区，利用lvm扩展即可

```
# xm list                      #下面对test2主机增大磁盘空间
Name                                        ID   Mem VCPUs      State   Time(s)
Domain-0                                     0  1024     4     r-----     80.8
test2                                        1   768     4     -b----     25.8
  
# qemu-img info test2.qcow2    #test2主机现在为10G的磁盘
image: test2.qcow2
file format: raw
virtual size: 10G (10739318784 bytes)  
disk size: 1.5G
  
# qemu-img create -f qcow2 -o size=5G,preallocation=metadata /data/testadd.qcow2  #新建一块5G的磁盘，等会添加此磁盘文件
Formatting '/data/testadd.qcow2', fmt=qcow2 size=5368709120 encryption=off 
cluster_size=65536 preallocation='metadata'
#防止出错，把preallocation=metadata去掉，或者qemu-img create -f raw /data/testadd.img 5G 这样更靠谱
  
# qemu-img info testadd.qcow2   #查看新建的磁盘
image: testadd.qcow2
file format: qcow2
virtual size: 5.0G (5368709120 bytes)
disk size: 912K
cluster_size: 65536
  
# virsh attach-disk test2 /data/testadd.qcow2 xvdb --cache=writeback --subdriver=qcow2  #对test2主机进行添加，xvdb
Disk attached successfully
  
 
# vim test2          #修改guest的配置文件，添加xvdb
name = "test2"
memory = "768"
disk = [ "file:/data/test2.qcow2,xvda,w","file:/data/testadd.qcow2,xvdb,w" ] #原来配置文件只有test2.qcow2,xvda 一块虚拟磁盘
vif = [ "bridge=br0" ]
vcpus = 4
on_reboot = "restart"
on_crash = "destroy"
```

添加完磁盘文件，需要在主机内分区，

### 扩展lvm

```
# fdisk -l                    #查看有没有刚添加的xvdb
Disk /dev/xvdb: 5369 MB, 5369757696 bytes
  
   
# fdisk /dev/xvdb             #进行分区，lvm格式
Command (m for help): n
Command action
   e   extended
   p   primary partition (1-4)
p
  
Partition number (1-4): 1
First cylinder (1-652, default 1): 
Using default value 1
Last cylinder, +cylinders or +size{K,M,G} (1-652, default 652): 
Using default value 652
  
Command (m for help): t
Selected partition 1
Hex code (type L to list codes): 8e
Changed system type of partition 1 to 8e (Linux LVM)
  
Command (m for help): p
  
Disk /dev/xvdb: 5369 MB, 5369757696 bytes
255 heads, 63 sectors/track, 652 cylinders
Units = cylinders of 16065 * 512 = 8225280 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0xb1ef0943
  
    Device Boot      Start         End      Blocks   Id  System
/dev/xvdb1               1         652     5237158+  8e  Linux LVM
  
Command (m for help): w
The partition table has been altered!
  
Calling ioctl() to re-read partition table.
Syncing disks.
```

### 对lvm格式磁盘增加空间

```
[root@localhost ~]# partx -a /dev/xvdb
BLKPG: Device or resource busy
error adding partition 1
[root@localhost ~]# kpartx /dev/xvdb
xvdb1 : 0 10474317 /dev/xvdb 63
[root@localhost ~]# partx -a /dev/xvdb1 /dev/xvdb
[root@localhost ~]# pvcreate /dev/xvdb1 
  Physical volume "/dev/xvdb1" successfully created    #主要是出来这条信息
   
[root@localhost ~]# vgs             #现在为10G的磁盘
  VG       #PV #LV #SN Attr   VSize VFree
  VolGroup   1   2   0 wz--n- 9.51g    0 
   
[root@localhost ~]# vgextend VolGroup /dev/xvdb1 
  Volume group "VolGroup" successfully extended
   
[root@localhost ~]# vgs              #增大了5G的空间       
  VG       #PV #LV #SN Attr   VSize  VFree
  VolGroup   2   2   0 wz--n- 14.50g 4.99g
   
[root@localhost ~]# lvs
  LV      VG       Attr      LSize   Pool Origin Data%  Move Log Cpy%Sync Convert
  lv_root VolGroup -wi-ao---   8.54g                                             
  lv_swap VolGroup -wi-ao--- 992.00m                                             
   
[root@localhost ~]# df -h
Filesystem            Size  Used Avail Use% Mounted on
/dev/mapper/VolGroup-lv_root
                      8.5G  695M  7.3G   9% /
tmpfs                 371M     0  371M   0% /dev/shm
/dev/xvda1            485M   32M  429M   7% /boot
  
[root@localhost ~]# lvextend -l +100%FREE /dev/VolGroup/lv_root 
  Extending logical volume lv_root to 13.53 GiB
  Logical volume lv_root successfully resized
  
[root@localhost ~]# resize2fs /dev/VolGroup/lv_root 
resize2fs 1.41.12 (17-May-2010)
Filesystem at /dev/VolGroup/lv_root is mounted on /; on-line resizing required
old desc_blocks = 1, new_desc_blocks = 1
Performing an on-line resize of /dev/VolGroup/lv_root to 3547136 (4k) blocks.
The filesystem on /dev/VolGroup/lv_root is now 3547136 blocks long.
  
[root@localhost ~]# df -h            #磁盘增加好了
Filesystem            Size  Used Avail Use% Mounted on
/dev/mapper/VolGroup-lv_root
                       14G  698M   12G   6% /
tmpfs                 371M     0  371M   0% /dev/shm
/dev/xvda1            485M   32M  429M   7% /boot
```

XFS磁盘扩容：

给磁盘增大了空间，比如30G增大到100G，系统：centos 7.4，系统磁盘为/dev/sda

```
# fdisk -l
   Device Boot      Start         End      Blocks   Id  System
/dev/sda1   *        2048     1026047      512000   83  Linux
/dev/sda2         1026048    62914559    30944256   8e  Linux LVM
# df -Th
Filesystem               Size  Used Avail Use% Mounted on
/dev/mapper/centos-root   30G  1.1G   29G   4% /
devtmpfs                 1.9G     0  1.9G   0% /dev
tmpfs                    1.9G     0  1.9G   0% /dev/shm
tmpfs                    1.9G  8.5M  1.9G   1% /run
tmpfs                    1.9G     0  1.9G   0% /sys/fs/cgroup
/dev/sda1                497M  136M  362M  28% /boot
tmpfs                    389M     0  389M   0% /run/user/0
```

可以看到sda1是boot分区，sda2是/ 根分区，现在对这个磁盘做了扩容，总大小为100G

![kvm和Xen主机在线增加磁盘空间 - 第1张](../images/2016/03/%E5%BE%AE%E4%BF%A1%E6%88%AA%E5%9B%BE_20180530134754.png)

ok，下面开始

```
# fdisk /dev/sda
n
p
 
 
t
 
8e
p
   Device Boot      Start         End      Blocks   Id  System
/dev/sda1   *        2048     1026047      512000   83  Linux
/dev/sda2         1026048    62914559    30944256   8e  Linux LVM
/dev/sda3        62914560   209715199    73400320   8e  Linux LVM
w
```

```
# kpartx /dev/sda
sda1 : 0 1024000 /dev/sda 2048
sda2 : 0 61888512 /dev/sda 1026048
sda3 : 0 146800640 /dev/sda 62914560
# partx -a /dev/sda3 /dev/sda
# ls /dev/sda3
/dev/sda3
```

```
# pvdisplay 
  --- Physical volume ---
  PV Name               /dev/sda2
  VG Name               centos
  PV Size               29.51 GiB / not usable 3.00 MiB
  Allocatable           yes (but full)
  PE Size               4.00 MiB
  Total PE              7554
  Free PE               0
  Allocated PE          7554
  PV UUID               FhZYLH-lQ1c-ZIMR-I7ej-2FuX-cVok-20b2qD
   
  "/dev/sda3" is a new physical volume of "70.00 GiB"
  --- NEW Physical volume ---
  PV Name               /dev/sda3
  VG Name               
  PV Size               70.00 GiB
  Allocatable           NO
  PE Size               0   
  Total PE              0
  Free PE               0
  Allocated PE          0
  PV UUID               16xohH-QUYI-2wWP-9KDS-w9Ex-f6TK-e1Ka3v
 
# vgs
  VG     #PV #LV #SN Attr   VSize   VFree
  centos   1   1   0 wz--n- <29.51g    0 
# pvcreate /dev/sda3 
  Physical volume "/dev/sda3" successfully created.
# vgextend centos /dev/sda3 
  Volume group "centos" successfully extended
# vgs
  VG     #PV #LV #SN Attr   VSize  VFree  
  centos   2   1   0 wz--n- 99.50g <70.00g
# vgdisplay 
  --- Volume group ---
  VG Name               centos
  System ID             
  Format                lvm2
  Metadata Areas        2
  Metadata Sequence No  4
  VG Access             read/write
  VG Status             resizable
  MAX LV                0
  Cur LV                1
  Open LV               1
  Max PV                0
  Cur PV                2
  Act PV                2
  VG Size               99.50 GiB
  PE Size               4.00 MiB
  Total PE              25473
  Alloc PE / Size       25473 / 99.50 GiB
  Free  PE / Size       0 / 0   
  VG UUID               14wUoX-TqWC-2184-RTcc-fyDO-m9XP-fBB0nV
 
# lvextend -l +100%FREE /dev/centos/root 
  Size of logical volume centos/root changed from <29.51 GiB (7554 extents) to 99.50 GiB (25473 extents).
  Logical volume centos/root successfully resized.
# lvdisplay 
  --- Logical volume ---
  LV Path                /dev/centos/root
  LV Name                root
  VG Name                centos
  LV UUID                MkjSKD-Xj3o-BMEk-w2zc-BnQY-qH3f-vQPeSs
  LV Write Access        read/write
  LV Creation host, time localhost.localdomain, 2018-04-03 17:33:59 +0800
  LV Status              available
  # open                 1
  LV Size                99.50 GiB
  Current LE             25473
  Segments               2
  Allocation             inherit
  Read ahead sectors     auto
  - currently set to     8192
  Block device           253:0
 
# xfs_growfs /dev/centos/root 
meta-data=/dev/mapper/centos-root isize=512    agcount=4, agsize=1933824 blks
         =                       sectsz=512   attr=2, projid32bit=1
         =                       crc=1        finobt=0 spinodes=0
data     =                       bsize=4096   blocks=7735296, imaxpct=25
         =                       sunit=0      swidth=0 blks
naming   =version 2              bsize=4096   ascii-ci=0 ftype=1
log      =internal               bsize=4096   blocks=3777, version=2
         =                       sectsz=512   sunit=0 blks, lazy-count=1
realtime =none                   extsz=4096   blocks=0, rtextents=0
data blocks changed from 7735296 to 26084352
 
# df -Th
Filesystem              Type      Size  Used Avail Use% Mounted on
/dev/mapper/centos-root xfs       100G  1.1G   99G   2% /
devtmpfs                devtmpfs  1.9G     0  1.9G   0% /dev
tmpfs                   tmpfs     1.9G     0  1.9G   0% /dev/shm
tmpfs                   tmpfs     1.9G  8.5M  1.9G   1% /run
tmpfs                   tmpfs     1.9G     0  1.9G   0% /sys/fs/cgroup
/dev/sda1               xfs       497M  136M  362M  28% /boot
tmpfs                   tmpfs     389M     0  389M   0% /run/user/0
```

另外执行fdisk -l,或 blkid 遇到一个小提示：

kernel: blk_update_request: I/O error, dev fd0, sector 0

因为是虚拟机，默认bios里面有floppy，所以执行blkid，或者fdisk -l 都会触发fd0（就是floppy）IO错误，在bios里面关闭floppy后不会有这个提示

### **KVM的guest热扩充磁盘**

```
[root@localhost ~]# virsh list
 Id    Name                           State
----------------------------------------------------
 1     devops2u                         running
  
# qemu-img info devops2u.qcow2 
image: devops2u.qcow2
file format: qcow2
virtual size: 10G (10737418240 bytes)
disk size: 1.3G
cluster_size: 65536
  
# qemu-img create -f qcow2 -o size=5G,preallocation=metadata /var/kvm/devops2u_add.qcow2
Formatting '/var/kvm/devops2u_add.qcow2', fmt=qcow2 size=5368709120 encryption=off cluster_size=65536 preallocation='metadata' 
#防止出错，把preallocation=metadata去掉，或者qemu-img create -f raw /var/kvm/devops2u_add.img 5G 
  
# virsh attach-disk devops2u /var/kvm/devops2u_add.qcow2 vdb --cache=writeback --subdriver=qcow2
Disk attached successfully
  
# virsh edit devops2u
<devices>                          #这一块是现在已有的磁盘文件
    <emulator>/usr/libexec/qemu-kvm</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='writeback'/>
      <source file='/var/kvm/devops2u.qcow2'/>
      <target dev='vda' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
    </disk>
##下面为添加的磁盘文件
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='writeback'/>
      <source file='/var/kvm/devops2u_add.qcow2'/>          #指定路径
      <target dev='vdb' bus='virtio'/>                      #指定磁盘名称vdb
      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/> 
 #slot和其他的设备序列不要相同，如果相同，保存的时候会有提示
   </disk>
```

虚拟主机里面终端会有pci日志提示。和xen主机扩展lvm磁盘格式一样，

```
# df -h
Filesystem                    Size  Used Avail Use% Mounted on
/dev/mapper/VolGroup-lv_root  8.4G  918M  7.1G  12% /
tmpfs                         372M     0  372M   0% /dev/shm
/dev/vda1                     485M   32M  428M   7% /boot
  
# fdisk -l
Disk /dev/vdb: 5368 MB, 5368709120 bytes
   
[root@localhost ~]# lvs
  LV      VG       Attr       LSize Pool Origin Data%  Move Log Cpy%Sync Convert
  lv_root VolGroup -wi-ao---- 8.51g                                             
  lv_swap VolGroup -wi-ao---- 1.00g                                             
   
[root@localhost ~]# vgextend VolGroup /dev/vdb
  No physical volume label read from /dev/vdb
  Physical volume /dev/vdb not found
  Physical volume "/dev/vdb" successfully created
  Volume group "VolGroup" successfully extended
  
[root@localhost ~]# lvextend -l +100%FREE /dev/mapper/VolGroup-lv_root
  Extending logical volume lv_root to 13.50 GiB
  Logical volume lv_root successfully resized
   
[root@localhost ~]# resize2fs /dev/mapper/VolGroup-lv_root
resize2fs 1.41.12 (17-May-2010)
Filesystem at /dev/mapper/VolGroup-lv_root is mounted on /; on-line resizing required
old desc_blocks = 1, new_desc_blocks = 1
Performing an on-line resize of /dev/mapper/VolGroup-lv_root to 3539968 (4k) blocks.
The filesystem on /dev/mapper/VolGroup-lv_root is now 3539968 blocks long.
   
[root@localhost ~]# df -h
Filesystem                    Size  Used Avail Use% Mounted on
/dev/mapper/VolGroup-lv_root   14G  920M   12G   8% /
tmpfs                         372M     0  372M   0% /dev/shm
/dev/vda1                     485M   32M  428M   7% /boot
```

扩充磁盘空间需要在业务量最低的时候，因为此时磁盘IO最大，在线服务必然受到影响

上面是主机一直在运行的情况下增加磁盘空间。如果主机可以重启的话，就没有什么可担忧的了。

### **重启方式增大磁盘空间**

```
qcow2格式磁盘增大空间：
# qemu-img create -f qcow2 -o size=100G,preallocation=metadata /var/xen/centos3.qcow2
  
# qemu-img info centos3.qcow2
image: centos3.qcow2
file format: qcow2
virtual size: 100G (107374182400 bytes)
disk size: 49G
cluster_size: 65536
#已经是100G空间的guest主机，下面再增大100G空间
  
# qemu-img resize centos3.qcow2 +100G                 #增加100G空间
# qemu-img info centos3.qcow2
image: centos3.qcow2
file format: qcow2
virtual size: 200G (214748364800 bytes)
disk size: 49G
cluster_size: 65536
  
#img格式增大硬盘容量：
dd if=/dev/zero bs=8k count=125000 >> /data/centos65.img
125000+0 records in
125000+0 records out
1024000000 bytes (1.0 GB) copied, 14.1461 s, 72.4 MB/s
```

进入guest主机，如上Xen主机扩充磁盘的方式进行添加。

也可以进入guest主机，把新添加的磁盘文件分区后新建文件夹，进行挂载

```
# fdisk -l
# fdisk /dev/xvdb
# partx -a /dev/xvdb
BLKPG: Device or resource busy
error adding partition 1
# kpartx /dev/xvdb
xvdb1 : 0 4294961622 /dev/xvdb 63
# partx -a /dev/xvdb1 /dev/xvdb
# mkfs.ext4 /dev/xvdb1
# mkdir /data
# vim /etc/fstab
/dev/xvdb1 /data ext4 defaults 0 0
# mount -a
# df -h
```

qcow2文件只能增大不能减小，一般的线上服务，都有高可用，磁盘不够用了，直接重做guest，简单粗暴

2016年03月28日 于 [linux工匠](http://www.bbotte.com/) 发表