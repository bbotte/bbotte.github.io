---
layout: default
---

# linux工匠之kubernetes使用ceph块存储

### 说明

接上篇文章[linux工匠之ceph存储集群实验](http://bbotte.com/server-config/ceph-storage-cluster-experiment/)，ceph官方文档中介绍Ceph FS 还不像 Ceph 块设备和 Ceph 对象存储那么稳定，所以我们用ceph块存储作为kubernetes的存储

kubernetes node节点主机操作：
kubernetes node节点需要安装ceph，

```
yum install -y https://download.ceph.com/rpm-jewel/el7/noarch/ceph-release-1-0.el7.noarch.rpm
yum -y install ceph-common
```

ceph-deploy主机操作：
ceph块存储主机名为ceph-client，在ceph-deploy节点部署配置，并把ceph.client.admin.keyring推送到kubernetes node节点主机

```
ceph-deploy install ceph-client
ceph-deploy admin ceph-client
scp /etc/ceph/ceph.client.admin.keyring kubernetes_node_IP(kubernetes node节点主机IP):/etc/ceph/
```

```
# ceph -s
    cluster 84829cda-5147-4b0b-92d1-7e46713d4e72
     health HEALTH_OK
     monmap e1: 1 mons at {node1=192.168.22.62:6789/0}
            election epoch 3, quorum 0 node1
     osdmap e39: 2 osds: 2 up, 2 in
            flags sortbitwise,require_jewel_osds
      pgmap v2932: 120 pgs, 8 pools, 1870 MB data, 652 objects
            16627 MB used, 18160 MB / 34788 MB avail
                 120 active+clean
```

查看admin.keyring的base64格式，因为ceph-secret.yaml配置文件需要

```
# grep key ceph.client.admin.keyring |awk '{printf "%s", $NF}'|base64
QVFBS1hvRmFxZVNLTVJBQWN1b0lZVFJUM2FWZDlObUJuZGprWFE9PQ==
```

### 新建块设备

ceph块存储主机操作：
创建一个2G大小的块设备

```
# rbd create clientrbd --size 2048
# rbd feature disable clientrbd exclusive-lock, object-map, fast-diff, deep-flatten
ceph --show-config|grep features 查看，或者更改ceph.conf配置，添加
rbd_default_features = 1
或者
rbd create clientrbd --size 2G --image-feature layering
# rbd map clientrbd --name client.admin
/dev/rbd0
# rbd list
clientrbd
# rbd info 'clientrbd'
rbd image 'clientrbd':
	size 2048 MB in 512 objects
	order 22 (4096 kB objects)
	block_name_prefix: rbd_data.107074b0dc51
	format: 2
	features: layering
	flags: 
# rados lspools
rbd
.rgw.root
default.rgw.control
default.rgw.data.root
default.rgw.gc
default.rgw.log
default.rgw.users.uid
默认在rbd的pool里面
 
# rbd showmapped
id pool image     snap device    
0  rbd  clientrbd -    /dev/rbd0
```

kubernetes主节点操作：

### 创建ceph配置

```
# ls
ceph-secret.yaml rbd.yaml
```

```
# cat ceph-secret.yaml 
apiVersion: v1
kind: Secret
metadata:
  name: ceph-secret
type: "kubernetes.io/rbd"  
data:
  key: QVFBS1hvRmFxZVNLTVJBQWN1b0lZVFJUM2FWZDlObUJuZGprWFE9PQ==
```

```
# cat rbd.yaml 
{
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": "rbd"
    },
    "spec": {
        "containers": [
            {
                "name": "rbd-rw",
                "image": "kubernetes/pause",
                "volumeMounts": [
                    {
                        "mountPath": "/mnt/rbd",
                        "name": "rbdpd"
                    }
                ]
            }
        ],
        "volumes": [
            {
                "name": "rbdpd",
                "rbd": {
                    "monitors": [
        						"192.168.22.62:6789"
    				 ],
                    "pool": "rbd",
                    "image": "clientrbd",
                    "user": "admin",
                    "keyring": "/etc/ceph/ceph.client.admin.keyring",
                    "fsType": "ext4",
                    "readOnly": true
                }
            }
        ]
    }
}
```

```
# kubectl create -f ceph-secret.yaml 
secret "ceph-secret" created
# kubectl create -f rbd.yaml 
pod "rbd" created
# kubectl get po
NAME      READY     STATUS    RESTARTS   AGE
rbd       1/1       Running   0          13s
```

### 验证块设备挂载

在kubernetes node节点查看挂载情况

```
# mount |grep rbd
/dev/rbd0 on /var/lib/kubelet/plugins/kubernetes.io/rbd/rbd/rbd-image-clientrbd type ext4 (ro,relatime,seclabel,stripe=1024,data=ordered)
/dev/rbd0 on /var/lib/kubelet/pods/cbb2720e-187c-11e8-a7b2-000c290ff3f0/volumes/kubernetes.io~rbd/rbdpd type ext4 (ro,relatime,seclabel,stripe=1024,data=ordered)
# df -h|grep rbd
/dev/rbd0                2.0G  6.0M  1.8G   1% /var/lib/kubelet/plugins/kubernetes.io/rbd/rbd/rbd-image-clientrbd
```

上面即ceph块设备作为kubernetes的存储，不过有个问题是当这个节点被删除后，挂载的内容也将丢失。为了容器重建后仍然可以使用之前的数据，kubernetes从v1.0版本引入PersistentVolume和PersistentVolumeClaim两个资源对象来实现对存储的管理。
**PV**是存储资源，包括存储能力（比如空间大小、IOPS）、访问模式(读写权限)、存储类型（StorageClass）、回收策略（保存、删除、回收空间）、后端存储类型等信息的设置。kubernetes支持PV类型有AWSElasticBlobStore、NFS、RBD(ceph块存储)、GlusterFS等
**PVC**是用户对存储资源的申请，即包括存储空间大小和访问模式(读写权限)、PV选择条件（通过Label Selector设置对PV筛选，根据标签选合适的PV与PVC进行绑定）、存储类型（StorageClass）
**StorageClass**是对存储资源的抽象定义，作用是屏蔽设置PVC等后端存储细节，由系统自动完成PV的创建和绑定，实现动态的资源供应，减少我们的工作。StorageClass包括名称、后端存储提供者、后端存储参数。一旦被创建出来将无法修改，只能删除

### **PV和PVC模式存储**

ceph-secret还是用上面那个ceph-secret.yaml,删除rbd.yaml

```
# kubectl delete -f rbd.yaml 
pod "rbd" deleted
```

在ceph-client块存储主机操作：

```
# rbd list
clientrbd
[root@ceph-client ~]# rbd rm clientrbd
2018-02-23 19:38:59.926432 7f2198e0ed80 -1 librbd: image has watchers - not removing
Removing image: 0% complete...failed.
rbd: error: image still has watchers
This means the image is still open or the client using it crashed. Try again after closing/unmapping it or waiting 30s for the crashed client to timeout.
```

下面是kubernetes的部署：

```
# cat ceph-pv.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: ceph-pv
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  rbd:
    monitors:
      - 192.168.22.62:6789
    pool: rbd
    image: clientrbd
    user: admin
    secretRef:
      name: ceph-secret
    fsType: ext4
    readOnly: false
  persistentVolumeReclaimPolicy: Recycle
```

```
# cat ceph-pvc.yaml
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: ceph-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

```
# cat ceph-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: ceph-pod
spec:
  containers:
  - name: busybox
    image: busybox
    command: ["sleep", "600"]
    volumeMounts:
    - name: ceph-vol
      mountPath: /opt/busybox
      readOnly: false
  volumes:
  - name: ceph-vol
    persistentVolumeClaim:
      claimName: ceph-pvc
```

```
# kubectl create -f ceph-pv.yaml
# kubectl create -f ceph-pvc.yaml
# kubectl get pv,pvc
NAME         CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS    CLAIM              STORAGECLASS   REASON    AGE
pv/ceph-pv   1Gi        RWO            Recycle          Bound     default/ceph-pvc                            52s
 
NAME           STATUS    VOLUME    CAPACITY   ACCESS MODES   STORAGECLASS   AGE
pvc/ceph-pvc   Bound     ceph-pv   1Gi        RWO                           48s
 
# kubectl create -f ceph-pod.yaml
# kubectl get po
NAME       READY     STATUS    RESTARTS   AGE
ceph-pod   1/1       Running   0          25s
```

到kubernetes node节点查看挂载情况

```
[root@node ~]# docker ps|grep busybox
b50aec50e721        busybox@sha256:1669a6aa789f19a090ac75b7083da748db   "sleep 600"              About a minute ago   Up About a minute                       k8s_busybox_ceph-pod_default_b3241888-188d-11e8-a7b2-000c290ff3f0_0
[root@node ~]# docker exec -it b50aec50e721 /bin/sh
/ # df -h|grep rbd
/dev/rbd0                 1.9G      6.0M      1.8G   0% /opt/busybox
/ # echo `date` > /opt/busybox/time
/ # ls /opt/busybox/
lost+found  time
```

kubernetes master节点删除ceph-pod，再创建，查看里面的文件是否丢失

```
# kubectl delete -f ceph-pod.yaml 
pod "ceph-pod" deleted
[root@master ceph]# kubectl create -f ceph-pod.yaml 
pod "ceph-pod" created
[root@master ceph]# kubectl get po 
NAME       READY     STATUS    RESTARTS   AGE
ceph-pod   1/1       Running   0          26s
```

到kubernetes node节点验证存储数据是否存在，下面证明存储的数据已经保留

```
# docker ps|grep busybox
d99e556a15dd        busybox@sha256:1669a6aa7350e1cdd28f972ddad5aceba2912f589f19a090ac75b7083da748db   "sleep 600"              44 seconds ago      Up 43 seconds                           k8s_busybox_ceph-pod_default_bdc5678d-188e-11e8-a7b2-000c290ff3f0_0
[root@node ~]# docker exec -it d99e556a15dd cat /opt/busybox/time
Fri Feb 23 11:39:45 UTC 2018
[root@node ~]# docker exec -it d99e556a15dd date
Fri Feb 23 11:44:18 UTC 2018
```

上面虽然设置的存储是1g,不过我测试写入文件可以超过1g

```
requests:
  storage: 1Gi
```

如果存储资源使用的是动态模式，即没有预先定义PV，仅通过StorageClass交给系统自动完成PV的动态创建，那么PVC再设定Selector时，系统无法分配存储资源。如需保留PV（用户数据），则在动态绑定后，需要将PV的回收策略从Delete改为Retain

### **StorageClass模式存储**

使用StorageClass模式不用预先创建固定大小的PV，直接配置PVC即可
先删除上面创建的PV、PVC、pod、ceph-secret

### 创建独立的rbd存储

ceph创建存储池kube

```
# ceph osd pool create kube 128
# ceph osd lspools
0 rbd,1 .rgw.root,2 default.rgw.control,3 default.rgw.data.root,4 default.rgw.gc,5 default.rgw.log,6 default.rgw.users.uid,7 data,8 kube,
```

ceph-deploy主机，创建client.kube用户并授权

```
# ceph auth get-or-create client.kube
[client.kube]
	key = AQBvz5Naabt+ABAAhb0ZKq4TyYOeERxe7HiYRw==
 
# ceph auth caps client.kube mon 'allow r' osd 'allow * pool=kube' mds 'allow * pool=kube'
updated caps for client.kube
# ceph auth get client.kube
exported keyring for client.kube
[client.kube]
	key = AQBvz5Naabt+ABAAhb0ZKq4TyYOeERxe7HiYRw==
	caps mds = "allow * pool=kube"
	caps mon = "allow r"
	caps osd = "allow * pool=kube"
# ceph auth get-key client.admin | base64
QVFBS1hvRmFxZVNLTVJBQWN1b0lZVFJUM2FWZDlObUJuZGprWFE9PQ==
# ceph auth get-key client.kube|base64
QVFCdno1TmFhYnQrQUJBQWhiMFpLcTRUeVlPZUVSeGU3SGlZUnc9PQ==
 
查看ceph集群上的所有用户权限列表
# ceph auth list
```

### StorageClass配置

```
# cat ceph-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ceph-admin-secret
  namespace: kube-system
type: "kubernetes.io/rbd"
data:
  # ceph auth get-key client.admin | base64
  key: QVFBS1hvRmFxZVNLTVJBQWN1b0lZVFJUM2FWZDlObUJuZGprWFE9PQ==
---
apiVersion: v1
kind: Secret
metadata:
  name: ceph-secret
  namespace: kube-system
type: "kubernetes.io/rbd"  
data:
  # ceph auth add client.kube mon 'allow r' osd 'allow rwx pool=kube'
  # ceph auth get-key client.kube | base64
  key: QVFCdno1TmFhYnQrQUJBQWhiMFpLcTRUeVlPZUVSeGU3SGlZUnc9PQ==
```

下面是pv、pvc、pod配置文件

```
# cat storageclass.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ceph-storageclass
provisioner: kubernetes.io/rbd
parameters:
  monitors: 192.168.22.62:6789
  adminId: admin
  adminSecretName: ceph-secret
  adminSecretNamespace: default
  pool: data
  userId: admin
  userSecretName: ceph-secret
```

```
# cat storageclass-pvc.yaml 
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: storageclass-pvc
  annotations: 
    volume.beta.kubernetes.io/storage-class: ceph-storageclass
spec:
  accessModes:
    - ReadWriteOnce 
  resources:
    requests:
      storage: 1Gi
```

```
# cat storageclass-pod.yaml 
apiVersion: apps/v1beta1
kind: Deployment
metadata:
  name: ceph-storageclass-pod
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
        command: ["sleep", "600"]
        volumeMounts:
        - name: ceph-storageclass-vol
          mountPath: /opt/busybox
          readOnly: false
      volumes:
      - name: ceph-storageclass-vol
        persistentVolumeClaim:
          claimName: storageclass-pvc
```

配置文件如上

### 创建PVC

```
# kubectl create -f storageclass.yaml
# kubectl get storageclass
# kubectl create -f storageclass-pvc.yaml
# kubectl get pvc
NAME               STATUS    VOLUME    CAPACITY   ACCESS MODES   STORAGECLASS        AGE
storageclass-pvc   Pending                                       ceph-storageclass   12s
# kubectl describe pvc storageclass-pvc
Name:          storageclass-pvc
Namespace:     default
StorageClass:  ceph-storageclass
Status:        Pending
Events:
  Type     Reason              Age               From                         Message
  ----     ------              ----              ----                         -------
  Warning  ProvisioningFailed  8s (x3 over 23s)  persistentvolume-controller  Failed to provision volume with StorageClass "ceph-storageclass": failed to create rbd image: executable file not found in $PATH, command output:
```

遇到错误：failed to create rbd image: executable file not found in $PATH，安装ceph-common也不行，因为kube-controller-manager使用容器方式运行，容器里面找不到rbd命令，也有把kube-controller-manager变为主机服务方式运行成功的，即：

3个方法：
1，用封装好的rbd运行在kubernetes节点上面，即第三方rbd-provisioner
2，kube-controller-manager由docker运行变为主机服务方式在master节点运行

3，更换kube-controller-manager镜像为quay.io/coreos/hyperkube

```
# kubectl logs kube-controller-manager-master -n kube-system
W0226 14:27:32.473036       1 rbd_util.go:395] failed to create rbd image, output 
E0226 14:27:32.473120       1 rbd.go:367] rbd: create volume failed, err: failed to create rbd image: executable file not found in $PATH, command output:
```

如果是kubernetes集群是主机安装模式（kubernetes不是docker运行）就不会有这个问题。另一个解决方法是用封装好的rbd运行在kubernetes节点上面，详见：

[RBD Volume Provisioner for Kubernetes](https://github.com/bbotte/external-storage/tree/master/ceph/rbd)

```
# cat account.yaml 
kind: ServiceAccount
apiVersion: v1
metadata:
  name: rbd-provisioner
  namespace: kube-system
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: rbd-provisioner
subjects:
- kind: ServiceAccount
  name: rbd-provisioner
  namespace: kube-system
roleRef:
  kind: ClusterRole
  name: system:controller:persistent-volume-binder
  apiGroup: rbac.authorization.k8s.io
 
 
# cat ceph-secret.yaml 
apiVersion: v1
kind: Secret
metadata:
  name: ceph-admin-secret
  namespace: kube-system
type: "kubernetes.io/rbd"
data:
  # ceph auth get-key client.admin | base64
  key: QVFBS1hvRmFxZVNLTVJBQWN1b0lZVFJUM2FWZDlObUJuZGprWFE9PQ==
---
apiVersion: v1
kind: Secret
metadata:
  name: ceph-secret
  namespace: kube-system
type: "kubernetes.io/rbd"  
data:
  # ceph auth add client.kube mon 'allow r' osd 'allow rwx pool=kube'
  # ceph auth get-key client.kube | base64
  key: QVFCdno1TmFhYnQrQUJBQWhiMFpLcTRUeVlPZUVSeGU3SGlZUnc9PQ==
 
 
# cat rbd-provisioner.yaml 
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: rbd-provisioner
spec:
  replicas: 2
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: rbd-provisioner
    spec:
      containers:
      - name: rbd-provisioner
        image: "quay.io/external_storage/rbd-provisioner:v0.1.1"
        env:
        - name: PROVISIONER_NAME
          value: ceph.com/rbd
      #serviceAccountName: rbd-provisioner
 
 
# cat storageclass.yaml 
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: rbd
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ceph.com/rbd
#provisioner: kubernetes.io/rbd
parameters:
  monitors: 192.168.22.62:6789
  pool: data
  adminId: admin
  adminSecretNamespace: kube-system
  adminSecretName: ceph-admin-secret
  userId: kube
  userSecretNamespace: kube-system
  userSecretName: ceph-secret
  imageFormat: "2"
  imageFeatures: layering
 
 
# cat storageclass-pvc.yaml 
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: testpvc
#  annotations: 
#    volume.beta.kubernetes.io/storage-class: teststorageclass
spec:
  storageClassName: rbd
  accessModes:
    - ReadWriteOnce 
  resources:
    requests:
      storage: 1Gi
 
 
# cat storageclass-pod.yaml 
apiVersion: apps/v1beta1
kind: Deployment
metadata:
  name: busybox
spec:
  strategy:
    type: Recreate
  replicas: 1
  template:
    metadata:
      labels:
        app: busybox
    spec:
      containers:
      - name: busybox
        image: busybox
        command: ["sleep", "600"]
        volumeMounts:
        - name: ceph-storageclass-vol
          mountPath: /opt/busybox
          readOnly: false
      volumes:
      - name: ceph-storageclass-vol
        persistentVolumeClaim:
          claimName: testpvc
```

rbd-provisioner服务是需要运行在kubernetes master节点(node节点运行会失败)，master节点需要允许建立节点

```
kubectl taint nodes --all node-role.kubernetes.io/master-
```

参考链接：

[ceph troublesshoot](https://github.com/att/netarbiter/blob/master/sds/ceph-docker/examples/helm/TROUBLESHOOT.md)

[Error creating rbd image: executable file not found in $PATH ](https://github.com/kubernetes/kubernetes/issues/38923)

[在Kubernetes中使用Sateful Set部署Redis](https://www.kubernetes.org.cn/2516.html)

[Kubernetes Storage Class](https://jicki.me/2017/09/11/kubernetes-storageclass/)

2018年02月27日 于 [linux工匠](http://www.bbotte.com/) 发表