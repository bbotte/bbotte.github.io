---
layout: default
---

# glusterfs在kubernetes中的使用详解

kubernetes集群的存储用什么，glusterfs、ceph、nfs、fastdfs？选择多了就会有困扰，各个集群都有自己的特点，gfs便于创建、维护，ceph支持比较广泛，nfs是许多存储自带的功能。我这里选择glusterfs，集群方式和RAID模式的原理一样，便于维护
下面为glusterfs集群创建完毕，可参考 [glusterfs集群故障恢复](https://bbotte.github.io/service_config/glusterfs-cluster-failure-recovery) ，先用静态模式做示例，再用动态模式storageclass示例，满足线上使用情况。

### **glusterfs静态配置**

```
# cat /etc/centos-release
CentOS Linux release 7.5.1804 (Core)
# cat /etc/hosts
192.168.0.224 gfs1
192.168.0.204 gfs2
```

先创建一个namespace，kubernetes默认的namespace为default

```
# cat gfs.yaml
apiVersion: v1
kind: Endpoints
metadata:
  name: gfs-ep
  namespace: default
subsets:
- addresses:
  - ip: 192.168.3.100
  - ip: 192.168.3.101
  - ip: 192.168.3.102
  ports:
  - port: 10
    protocol: TCP
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: glusterpv-def
  namespace: default
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteMany
  glusterfs:
    endpoints: "gfs-ep"  # 上面 Endpoints 名称
    path: "gfs"      # gluster volume create NAME, gfs创建存储的名字
    readOnly: false
---
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: gfspvc-def
  namespace: default
spec:
  accessModes:
    - ReadWriteMany
  volumeName: glusterpv-def
  resources:
    requests:
      storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: gfsdef-svc
  namespace: default
spec:
  ports:
  - port: 10
    protocol: TCP
    targetPort: 10
```

service和endpoint的name必须一致，endpoint中ip必须是ip，不能为hostname，端口port可以自己定义，不冲突即可

pv的配置中，endpoint即上面和service保持一致的endpoint名称
path是glusterfs的Volume Name(**gluster volume info 查看，或者 gluster volume list查看**)
pv定义的name和pvc的volumeName保持一致

```
# kubectl get pv,pvc
```

这时候，pvc就可以提供给kubernetes使用了，比如创建一个deployment的配置片段：

```
kind: Deployment
apiVersion: apps/v1beta2
metadata:
  name: something
  namespace: default
  labels:
    k8s-app: something
spec:
  replicas: 1
  selector:
    matchLabels:
      k8s-app: something
  template:
    metadata:
      labels:
        k8s-app: something
    spec:
      containers:
      - name: something
        image: harbor.bbotte.com/dev/task:pre-201808031033-ef5342ca
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 9001
        volumeMounts:
          - name: something-data-storage
            mountPath: /opt
      volumes:
      - name: something-data-storage
        persistentVolumeClaim:
          claimName: gfspvc-def
```

### **glusterfs动态配置**

首先需要说一下heketi，RESTful based volume management framework for GlusterFS，是给glusterfs存储提供RESTful API接口，这样kubernetes才可以调用存储
Heketi提供RESTful管理界面，可用于管理GlusterFS卷的生命周期。 借助Heketi，OpenStack Manila，Kubernetes和OpenShift等云服务可以使用任何支持的持久性类型动态配置GlusterFS卷。 Heketi将自动确定整个群集中bricks的位置，确保将bricks及其副本放置在不同的故障域中。 Heketi还支持任意数量的GlusterFS集群，允许云服务提供网络文件存储，而不限于单个GlusterFS集群。

前提是需要单独的磁盘，直接添加一块新的磁盘，不用格式化，下面例子为/dev/sdb， Heketi is currently limited to managing raw devices only, if a device is already a Gluster volume it will be skipped and ignored.
heketi后端默认的gfs集群为3个，所以下面创建3个gfs主机测试：

```
# yum install epel-release centos-release-gluster -y
# yum install heketi -y
# yum install heketi-client -y
# heketi -v
Heketi 7.0.0
heketi这台主机需要免秘钥登录gfs主机
# cat /etc/hosts
192.168.0.224 gfs1
192.168.0.204 gfs2
192.168.0.173 gfs3
# ssh-keygen -t rsa -N ''
# ssh-copy-id -i /root/.ssh/id_rsa.pub root@gfs1
# ssh-copy-id -i /root/.ssh/id_rsa.pub root@gfs2
# ssh-copy-id -i /root/.ssh/id_rsa.pub root@gfs3
 
# cp -r .ssh/ /opt/
# chown -R heketi:heketi /opt/.ssh
 
# cp /etc/heketi/heketi.json{,.bak}
systemctl restart heketi
```

messages提示：

```
heketi: Error: unknown shorthand flag: 'c' in -config=/etc/heketi/heketi.json
heketi: unknown shorthand flag: 'c' in -config=/etc/heketi/heketi.json
```

编辑/usr/lib/systemd/system/heketi.service
-config 改为 –config即可

```
systemctl restart heketi && systemctl status heketi && systemctl enable heketi
```

检查一下：

```
# curl localhost:8080/hello
Hello from Heketi
```

heketi-cli命令使用帮助

```
# heketi-cli -h
```

接着我们需要创建heketi的配置文件，配置文件中包含gfs主机的hostname/ip/drivers，其中/dev/sdb 磁盘空间为16G

```
# cat heketi-topology.json
{
  "clusters": [
    {
      "nodes": [
        {
          "node": {
            "hostnames": {
              "manage": [
                "gfs1"
              ],
              "storage": [
                "192.168.0.224"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb"
          ]
        },
        {
          "node": {
            "hostnames": {
              "manage": [
                "gfs2"
              ],
              "storage": [
                "192.168.0.204"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb"
          ]
        },
        {
          "node": {
            "hostnames": {
              "manage": [
                "gfs3"
              ],
              "storage": [
                "192.168.0.173"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb"
          ]
        }
      ]
    }
  ]
}
```

```
# heketi-cli topology load --json=heketi-topology.json
	Found node gfs1 on cluster a9046fd17098f0d251cf5a2bbf44dfe4
		Adding device /dev/sdb ... OK
	Found node gfs2 on cluster a9046fd17098f0d251cf5a2bbf44dfe4
		Adding device /dev/sdb ... OK
	Found node gfs3 on cluster a9046fd17098f0d251cf5a2bbf44dfe4
		Adding device /dev/sdb ... OK
 
# heketi-cli topology info
 
Cluster Id: a9046fd17098f0d251cf5a2bbf44dfe4
 
    File:  true
    Block: true
 
    Volumes:
 
    Nodes:
 
	Node Id: 2ccce4a61c793db24cb8f442a20f5abc
	State: online
	Cluster Id: a9046fd17098f0d251cf5a2bbf44dfe4
	Zone: 1
	Management Hostnames: gfs1
	Storage Hostnames: 192.168.0.224
	Devices:
		Id:cd1f3199082705879710ac77ce6aea54   Name:/dev/sdb            State:online    Size (GiB):15      Used (GiB):0       Free (GiB):15      
			Bricks:
 
	Node Id: 357b9d5d69767c0a4f3dbf87ec333c89
	State: online
	Cluster Id: a9046fd17098f0d251cf5a2bbf44dfe4
	Zone: 1
	Management Hostnames: gfs2
	Storage Hostnames: 192.168.0.204
	Devices:
		Id:33b82ada0b6f71ddbf0591987d74256a   Name:/dev/sdb            State:online    Size (GiB):15      Used (GiB):0       Free (GiB):15      
			Bricks:
 
	Node Id: 6d16c9c97a4e329148729de548f9e160
	State: online
	Cluster Id: a9046fd17098f0d251cf5a2bbf44dfe4
	Zone: 1
	Management Hostnames: gfs3
	Storage Hostnames: 192.168.0.173
	Devices:
		Id:46ae4bcb4685d56ce3e9152686249fd9   Name:/dev/sdb            State:online    Size (GiB):15      Used (GiB):0       Free (GiB):15      
			Bricks:
```

或者

```
# heketi-cli -s http://localhost:8080 topology info
```

如此，heketi的拓扑结构就建立完成，下面创建虚拟的磁盘，大小为8G，副本集为3个

```
# heketi-cli volume create --size=8 --replica=3
Name: vol_0e242f31559b96102655188c1d87cc89
Size: 8
Volume Id: 0e242f31559b96102655188c1d87cc89
Cluster Id: a9046fd17098f0d251cf5a2bbf44dfe4
Mount: 192.168.0.224:vol_0e242f31559b96102655188c1d87cc89
Mount Options: backup-volfile-servers=192.168.0.204,192.168.0.173
Block: false
Free Size: 0
Block Volumes: []
Durability Type: replicate
Distributed+Replica: 3
 
# heketi-cli volume list
Id:0e242f31559b96102655188c1d87cc89    Cluster:a9046fd17098f0d251cf5a2bbf44dfe4    Name:vol_0e242f31559b96102655188c1d87cc89
 
# heketi-cli volume info 0e242f31559b96102655188c1d87cc89
 
# df -h|grep heketi
/dev/mapper/vg_cd1f3199082705879710ac77ce6aea54-brick_b4dab51cd5a2996c4f61783d8b342f99  8.0G   33M  8.0G   1% /var/lib/heketi/mounts/vg_cd1f3199082705879710ac77ce6aea54/brick_b4dab51cd5a2996c4f61783d8b342f99
```

编写kubernetes需要的配置文件

```
# cat storageclass.yaml
kind: StorageClass
apiVersion: storage.k8s.io/v1beta1
metadata:
  name: gfs-sc
  namespace: bbotte
provisioner: kubernetes.io/glusterfs
parameters:
  resturl: "http://192.168.0.224:8080" 
  restauthenabled: "false"
  #volumetype: "replicate:3"
 
# kubectl get sc -n bbotte
NAME            PROVISIONER               AGE
gfs-sc   kubernetes.io/glusterfs   13s
```

创建storageclass后，需要创建一个pvc:

```
# cat storage-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: bbotte-storageclass
  namespace: bbotte
  annotations:
    volume.beta.kubernetes.io/storage-class: gfs-sc
spec:
  accessModes:
   - ReadWriteMany
  resources:
    requests:
      storage: 6Gi
```

### 疑问

神奇的事情就这样发生了，/dev/sdb磁盘空间为16G，heketi-cli创建的volume为8G，pvc这里storage为6G，并且heketi查看volume，并且增加了一个volume，即 34a02ada5a99948f60a36e894a3dc2a8，如果这里pvc的storage大于6G，会创建失败，提示空间不足

The magical thing happened. The disk space of /dev/sdb in the heketi topology is 16G, the volume created by heketi-cli is 8G, the storage of pvc here is 6G, the volume is viewed using heketi-cli, and a volume is added, ie 34a02ada5a99948f60a36e894a3dc2a8 .If the storage of pvc is greater than 6G, it will fail to create, and the prompt space is insufficient.

```
# heketi-cli volume list
Id:0e242f31559b96102655188c1d87cc89    Cluster:a9046fd17098f0d251cf5a2bbf44dfe4    Name:vol_0e242f31559b96102655188c1d87cc89
Id:34a02ada5a99948f60a36e894a3dc2a8    Cluster:a9046fd17098f0d251cf5a2bbf44dfe4    Name:vol_34a02ada5a99948f60a36e894a3dc2a8
 
# heketi-cli volume info 34a02ada5a99948f60a36e894a3dc2a8
Name: vol_34a02ada5a99948f60a36e894a3dc2a8
Size: 7
Volume Id: 34a02ada5a99948f60a36e894a3dc2a8
Cluster Id: a9046fd17098f0d251cf5a2bbf44dfe4
Mount: 192.168.0.224:vol_34a02ada5a99948f60a36e894a3dc2a8
Mount Options: backup-volfile-servers=192.168.0.204,192.168.0.173
Block: false
Free Size: 0
Block Volumes: []
Durability Type: replicate
Distributed+Replica: 3
```

heketi日志的提示

```
heketi: [negroni] Started POST /volumes
heketi: [cca4b24ef5ec2c01fa9b502047347fa8] Replica 3
heketi: Using the following clusters: [a9046fd17098f0d251cf5a2bbf44dfe4]
heketi: brick_size = 8388608
heketi: sets = 1
heketi: num_bricks = 3
heketi: Allocating brick set #0
heketi: 0 / 3
heketi: expected space needed for amount=8388608 snapFactor=1 : 8433664
heketi: device cd1f3199082705879710ac77ce6aea54[8208384] > required size [8433664] ?
heketi: Unable to place a brick of size 8388608 & factor 1 on device cd1f3199082705879710ac77ce6aea54
heketi: expected space needed for amount=8388608 snapFactor=1 : 8433664
heketi: device 46ae4bcb4685d56ce3e9152686249fd9[8208384] > required size [8433664] ?
heketi: Unable to place a brick of size 8388608 & factor 1 on device 46ae4bcb4685d56ce3e9152686249fd9
heketi: expected space needed for amount=8388608 snapFactor=1 : 8433664
heketi: device 33b82ada0b6f71ddbf0591987d74256a[8208384] > required size [8433664] ?
heketi: Unable to place a brick of size 8388608 & factor 1 on device 33b82ada0b6f71ddbf0591987d74256a
heketi: Error detected.  Cleaning up volume cca4b24ef5ec2c01fa9b502047347fa8: Len(0)
heketi: No space, re-trying with smaller brick size
heketi: brick_size = 4194304
......
heketi: Error detected.  Cleaning up volume aaaa: Len(0)
heketi: No space, re-trying with smaller brick size
heketi: Minimum brick size limit reached.  Out of space.
heketi: Cluster  can not accommodate volume (Minimum brick size limit reached.  Out of space.), trying next cluster
heketi: Create Volume Build Failed: No space
heketi: [negroni] Completed 500 Internal Server Error in 23.44751ms
```

我们查看创建的pvc和storageclass

```
# kubectl get pvc -n bbotte
NAME                 STATUS    VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS    AGE
bbotte-storageclass    Bound     pvc-6711f400-a752-11e8-bf00-005056be75a3   7G         RWX            gfs-sc   15h
gfs-pvc              Bound     gfs-pv                              10Gi       RWX                            63d
# kubectl get pv -n bbotte
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS    CLAIM                       STORAGECLASS    REASON    AGE
pvc-6711f400-a752-11e8-bf00-005056be75a3   7G         RWX            Delete           Bound     bbotte/bbotte-storageclass        gfs-sc             15h
```

可以看到pv默认的RECLAIM POLICY回收策略是删除，对于重要的数据，比如zookeeper、kafka不能被删除的，需要更改策略为retain保留

```
# kubectl patch pv pvc-6711f400-a752-11e8-bf00-005056be75a3 -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'
# kubectl get pv -n bbotte
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS    CLAIM                       STORAGECLASS    REASON    AGE
pvc-6711f400-a752-11e8-bf00-005056be75a3   7G         RWX            Retain           Bound     bbotte/bbotte-storageclass        gfs-sc             15h
```

建一个pod测试一下

```
apiVersion: apps/v1beta1
kind: Deployment
metadata:
  name: busybox-pod
  namespace: bbotte
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: busybox
    spec:
      containers:
      - name: busybox
        image: busybox
        imagePullPolicy: IfNotPresent
        command: ["sleep", "3600"]
        volumeMounts:
		- name: gluster-dev-volume
          mountPath: /mnt/gfs
      volumes:
      - name: gluster-dev-volume
        persistentVolumeClaim:
          claimName: bbotte-storageclass
```

```
# kubectl get po -n bbotte
NAME                           READY     STATUS    RESTARTS   AGE
busybox-pod-55577c5445-cnqvw   1/1       Running   15         15h
# kubectl -n bbotte exec -it busybox-pod-55577c5445-cnqvw /bin/sh
/ # df -h
Filesystem                Size      Used Available Use% Mounted on
192.168.0.173:vol_34a02ada5a99948f60a36e894a3dc2a8
                          7.0G    104.3M      6.9G   1% /mnt/gfs
```

over,如此，就可以愉快的创建zookeeper了

### 遇到的问题

创建heketi拓扑的时候提示：

```
Adding device /dev/sdb ... Unable to add device: Can't open /dev/sdb exclusively.  Mounted filesystem?
```

```
解决方法：
dmsetup remove_all
dmsetup ls
df -h
umount /var/lib/heketi/mounts
rm -rf /var/lib/heketi/*
vim /etc/fstab 删除gfs选项
wipefs -af /dev/sdb
partprobe /dev/sdb
重启主机
```

黑人问号脸，为什么heketi创建volume空间和storageclass中pvc storage空间相加必须小于heketi drivers的磁盘空间？

参考 [gluster docs](https://github.com/gluster/gluster-kubernetes/blob/master/docs/examples/dynamic_provisioning_external_gluster/README.md)

2018年08月24日 于 [linux工匠](https://bbotte.github.io/) 发表