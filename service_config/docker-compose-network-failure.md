---
layout: default
---

#### 由docker-compose导致的网络故障

环境说明：

跳板机上以docker-compose运行挺多的运维服务，这台跳板机同时可以登录其他主机，使用的阿里云

故障：某天早上连不上其他主机，提示 Destination Host Unreachable

做了一些操作后，比如停止docker服务，iptables 清空，还是没有解决问题，重启跳板机，ping 其他主机提示目的不可达

```
64 bytes from 172.25.27.139: icmp_seq=21 ttl=63 time=1.48 ms
64 bytes from 172.25.27.139: icmp_seq=22 ttl=63 time=1.47 ms
64 bytes from 172.25.27.139: icmp_seq=23 ttl=63 time=1.46 ms
From 172.25.0.1 icmp_seq=24 Destination Host Unreachable
From 172.25.0.1 icmp_seq=25 Destination Host Unreachable
From 172.25.0.1 icmp_seq=26 Destination Host Unreachable
```

网上查询的结果是有可能docker的网络影响到主机的路由，查询路由

```
route -n

Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         10.4.255.253    0.0.0.0         UG    0      0        0 eth0
10.4.0.0        0.0.0.0         255.255.0.0     U     0      0        0 eth0
169.254.0.0     0.0.0.0         255.255.0.0     U     1002   0        0 eth0
172.17.0.0      0.0.0.0         255.255.0.0     U     0      0        0 br-b435843911cc
172.18.0.0      0.0.0.0         255.255.0.0     U     0      0        0 br-0a3c277df966
172.23.0.0      0.0.0.0         255.255.0.0     U     0      0        0 br-ffaa0000a438

```

172.23.0.0的网段和其他主机属于一个网段，是docker-compose占用了主机的网段导致网络不通

查询docker的ip地址，看看是哪个docker-compose引起的，找172.23.0.0这个网段，等会改动docker-compose的网络。找到这个服务，先停止

```
docker ps|awk 'NR>1{print $1}'|xargs docker inspect -f '{{.Name}} {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'

# 先停止服务
docker-compose down
```

还有一种方法查找docker使用的ip地址

```
docker network ls

route -n
```

查看br虚拟网络，brctl可以通过命令 yum install -y bridge-utils 安装

```
brctl show

bridge name     bridge id               STP enabled     interfaces
br-ffaa0000a438         8000.02422acd7a5d       no
```

现在的br网络已经没有服务占用，下面删除

```
ifconfig br-ffaa0000a438 down
brctl stp br-ffaa0000a438 off
brctl delbr br-ffaa0000a438

route -n 查询已经没有了
```

最后更改docker-compose的网段


```
version: '3'
services:
  something:
    container_name: something
    image: something:202304061400
    restart: always
    volumes:
      - /data/logs:/app/log
    extra_hosts:
      - "mysql-svc:10.20.100.100
    networks:
      - some

networks:
  some:
    driver: bridge
    ipam:
      driver: default
      config:
      - subnet: 192.168.20.0/24
```

更改网络配置后，再docker-compose up -d，查看服务的ip

参考 
- [network-tutorial-overlay](https://docs.docker.com/network/network-tutorial-overlay/)
