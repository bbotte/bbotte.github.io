# glusterfs集群故障恢复

glusterfs集群故障恢复
以2台主机最简单的副本方式举例，安装步骤如下，先配置hosts，主机名，安装gluster服务

```
OS: CentOS 7.4
cat > /etc/hosts <<EOF
192.168.0.198 master
192.168.0.199 slave
EOF
hostnamectl --static set-hostname master/slave
exec $SHELL
yum install centos-release-gluster -y
yum install -y glusterfs glusterfs-server glusterfs-fuse glusterfs-rdma glusterfs-geo-replication glusterfs-devel
systemctl start glusterd && systemctl enable glusterd && systemctl status glusterd
```

添加其他节点，创建volume并启动

```
gluster peer probe slave
mkdir /data
gluster peer status
gluster volume create gfs-volume replica 2 transport tcp master:/data slave:/data force
ls -a /data/
gluster volume info
gluster volume start gfs-volume
gluster volume info gfs-volume
```

其他主机挂载gfs

```
yum install centos-release-gluster -y
yum install -y glusterfs-fuse

cat /etc/hosts
192.168.1.1 master

cat > /etc/fstab <<EOF
master:gfs-volume /opt glusterfs defaults,_netdev 0 0
EOF
mount -a
```

假如slave主机挂掉，并且不能启动，有2种方式可以恢复，
1，再创建一台主机，保持主机名和ip同故障主机一致
2，新创建一台主机，替换故障的主机

方案1，如果还是用192.168.0.199 这个ip作为slave节点，先安装glusterfs服务，不用启动
既然slave挂了，那么先要找到slave主机gfs的uuid，在正常的节点查看，这里是在master节点

```
# cat /var/lib/glusterd/peers/*
uuid=090f4559-e1a4-43ed-8a3d-2edd4042ce50
state=3
hostname1=slave
```

在挂掉的slave主机编辑gfs配置后，启动gfs服务

```
# cat /var/lib/glusterd/glusterd.info 
UUID=090f4559-e1a4-43ed-8a3d-2edd4042ce50
operating-version=1
# systemctl start glusterd
```

加入集群，检查状态，如果不ok，那么多重启几次glusterfs

```
gluster peer status
gluster peer probe master
gluster peer status
systemctl restart glusterd
```

同步数据

```
gluster volume info
gluster volume sync master all
cat /var/lib/glusterd/glusterd.info 
查看 operating-version 这个数值已经变动
```

查看状态

```
gluster volume heal gfs-volume info
```



方案2，替代故障主机

创建主机，主机名比如为 three，ip为 192.168.0.200，在正常运行的gfs主机添加新主机,替换故障主机

```
gluster peer probe three
gluster volume replace-brick gfs-volume slave:data three:/data commit force
```

查看状态

```
gluster volume heal gfs-volume info
```

因为gfs模式为replica ，到这里也就结束了，如果是Distributed ，需要rebalance

```
gluster volume rebalance gfs-volume fix-layout start
```



附：
移除一个gfs节点Remove a brick

```
gluster volume remove-brick gfs-volume replica 1 slave:/data start
```

移除slave主机的数据，只保留1份，即master
查看移除的状态

```
gluster volume remove-brick gfs-volume replica 1 slave:/data status
```

添加一个副本

```
gluster volume add-brick gfs-volume replica 2 slave:/data
```

参考文档

[Managing GlusterFS Volumes](https://docs.gluster.org/en/latest/Administrator%20Guide/Managing%20Volumes/)
[GlusterFS Architecture](https://docs.gluster.org/en/latest/Quick-Start-Guide/Architecture/)

2018年08月06日 于 [linux工匠](http://www.bbotte.com/) 发表

