---
layout: default
---

# NAT模式的LVS和keepalived高可用

1. 说明
2. 安装lvs和keepalived
3. DR主节点和备节点配置
4. Real Server配置
5. 查看信息
6. 测试

LVS+keepalived是公司里面常用的负载均衡和高可用实现方案，lvs支持3中模式：NAT，DR，Tun，下面是NAT模式的实现

### **说明**

CentOS6.5 64位  keepalived-1.2.13  ipvsadm v1.26  NAT模式

<http://zh.linuxvirtualserver.org/>

<http://keepalived.org/>

<http://www.linuxvirtualserver.org/Documents.html>

<http://www.austintek.com/LVS/LVS-HOWTO/HOWTO/index.html>

lvs服务器2块网卡，real server单网卡，ip如下：

```
主DR  192.168.22.219
eth0 外网192.168.22.219  192.168.22.249(VIP)
eth1 内网192.168.1.1        192.168.1.5(GateWay)
 
备DR   192.168.22.203
eth0 外网192.168.22.203  192.168.22.249(VIP)
eth1 内网192.168.1.2        192.168.1.5(GateWay)
 
realserver1  192.168.1.3    192.168.1.5(GateWay)
realserver2  192.168.1.4    192.168.1.5(GateWay)
```

```
           client
             |
       keepalived VIP
             |          
        -------------
        |           |
  LVS master      LVS backup
        |           |
        -------------
              |
          GateWay(虚拟)
              |          
        -------------
        |           |   
  Real Server1     Real Server2
```

### **安装lvs和keepalived**

```
yum install popt popt-devel popt-static libnl libnl-devel
yum install ipvsadm
tar -xzf keepalived-1.2.13.tar.gz
cd keepalived-1.2.13
./configure
make
make install
cp /usr/local/etc/rc.d/init.d/keepalived /etc/rc.d/init.d/
chmod +x /etc/rc.d/init.d/keepalived
cp /usr/local/etc/sysconfig/keepalived /etc/sysconfig/keepalived
cp /usr/local/sbin/keepalived /usr/sbin/keepalived
cp /usr/local/etc/keepalived/keepalived.conf /etc/keepalived/
mv /etc/keepalived/keepalived.conf /etc/keepalived/keepalived.conf.bak
```

开启IP转发

net.ipv4.ip_forward=1

### **DR主节点和备节点配置**

keepalived.conf配置

```
# vim /etc/keepalived/keepalived.conf
global_defs {
        notification_email {
        your_email@163.com
        }
  notification_email_from root@localhost
  smtp_server 127.0.0.1
  smtp_connect_timeout 30
  router_id lvs_dr1
}
vrrp_sync_group lvs_1 {
        group {
                VI_1
                VI_GATEWAY
                }
        notify_master "/usr/local/sbin/lvsdr.sh start"
        notify_backup "/usr/local/sbin/lvsdr.sh stop"
}
vrrp_instance VI_1 {
  state MASTER                 #backup为BACKUP
  interface eth0
  virtual_router_id 51
  priority 101                 #backup为100
  advert_int 1
  authentication {
        auth_type PASS
        auth_pass bbotte
        }
  virtual_ipaddress {
        192.168.22.249 255.255.255.0
        }
vrrp_instance VI_GATEWAY {
    state MASTER              #backup为BACKUP
    interface eth1
    virtual_router_id 52
    priority 101              #backup为100
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass bbotte
     }
     virtual_ipaddress {
          192.168.1.5
     }
  }
}
virtual_server 192.168.1.5 80
{
  delay_loop 2
  lb_algo rr
  lb_kind DR
  nat_mask 255.255.255.0
  persistence_timeout 60
  protocol TCP
  real_server 192.168.1.3 80
  {
        weight 1
        TCP_CHECK
        {
        connect_timeout 5
        nb_get_retry 3
        delay_before_retry 3
        connect_port 80
        }
  }
  real_server 192.168.1.4 80
  {
        weight 1
        TCP_CHECK
        {
        connect_timeout 5
        nb_get_retry 3
        delay_before_retry 3
        connect_port 80
        }
  }
}
```

```
vim /usr/local/sbin/lvsdr.sh
#!/bin/bash
## LVS script for VS/DR
. /etc/rc.d/init.d/functions
#
VIP=192.168.22.249
RIP1=192.168.1.3
RIP2=192.168.1.4
#
case "$1" in
start)
  /sbin/ifconfig eth0:1 $VIP netmask 255.255.255.0 up
# Since this is the Director we must be able to forward packets
  echo 1 > /proc/sys/net/ipv4/ip_forward
# Clear all iptables rules.
  /sbin/iptables -F
# Reset iptables counters.
  /sbin/iptables -Z
# Clear all ipvsadm rules/services.
  /sbin/ipvsadm -C
# Add an IP virtual service for VIP 192.168.0.200 port 80
# In this recipe, we will use the round-robin scheduling method.
# In production, however, you should use a weighted, dynamic scheduling method.
  /sbin/ipvsadm -A -t $VIP:80 -s rr
# Now direct packets for this VIP to
# the real server IP (RIP) inside the cluster
  /sbin/ipvsadm -a -t $VIP:80 -r $RIP1 -m
  /sbin/ipvsadm -a -t $VIP:80 -r $RIP2 -m
  
  /bin/touch /var/lock/subsys/ipvsadm.lock
;;
stop)
# Stop forwarding packets
  echo 0 > /proc/sys/net/ipv4/ip_forward
# Reset ipvsadm
  /sbin/ipvsadm -C
# Bring down the VIP interface
  ifconfig eth0:1 down
  
  rm -rf /var/lock/subsys/ipvsadm.lock
;;
status)
  [ -e /var/lock/subsys/ipvsadm.lock ] && echo "ipvs is running..." || echo "ipvsadm is stopped..."
;;
*)
  echo "Usage: $0 {start|stop}"
;;
esac
```

### **Real Server配置**

下面配置2台real server

两台机均为centos 6.5 yum安装httpd服务并启动，iptables对80端口开放

```
Real Server 1:
cat /var/www/html/index.html
web 1111111111111
 
Real Server 2:
cat /var/www/html/index.html
test 22222222222
```

开启IP转发

net.ipv4.ip_forward=1

配置网关

＃vim /etc/sysconfig/network-scripts/ifcfg-eth0添加

GATEWAY=”192.168.1.5″

realserver.sh相同，并启动此脚本

```
vim realserver.sh
#!/bin/bash
#
# Script to start LVS DR real server.
# description: LVS DR real server
#
. /etc/rc.d/init.d/functions
VIP=192.168.22.249
host=`/bin/hostname`
case "$1" in
start)
       # Start LVS-DR real server on this machine.
        /sbin/ifconfig lo down
        /sbin/ifconfig lo up
        echo 1 > /proc/sys/net/ipv4/conf/lo/arp_ignore
        echo 2 > /proc/sys/net/ipv4/conf/lo/arp_announce
        echo 1 > /proc/sys/net/ipv4/conf/all/arp_ignore
        echo 2 > /proc/sys/net/ipv4/conf/all/arp_announce
        /sbin/ifconfig lo:0 $VIP broadcast $VIP netmask 255.255.255.255 up
        /sbin/route add -host $VIP dev lo:0
;;
stop)
        # Stop LVS-DR real server loopback device(s).
        /sbin/ifconfig lo:0 down
        echo 0 > /proc/sys/net/ipv4/conf/lo/arp_ignore
        echo 0 > /proc/sys/net/ipv4/conf/lo/arp_announce
        echo 0 > /proc/sys/net/ipv4/conf/all/arp_ignore
        echo 0 > /proc/sys/net/ipv4/conf/all/arp_announce
;;
status)
        # Status of LVS-DR real server.
        islothere=`/sbin/ifconfig lo:0 | grep $VIP`
        isrothere=`netstat -rn | grep "lo:0" | grep $VIP`
        if [ ! "$islothere" -o ! "isrothere" ];then
            # Either the route or the lo:0 device
            # not found.
            echo "LVS-DR real server Stopped."
        else
            echo "LVS-DR real server Running."
        fi
;;
*)
            # Invalid entry.
            echo "$0: Usage: $0 {start|status|stop}"
            exit 1
;;
esac
```

### **查看信息**

DR MASTER：

```
# ip a
eth0  
    inet 192.168.22.219/24 brd 192.168.22.255
    inet 255.255.255.0/32
    inet 192.168.22.249/24 brd 192.168.22.255
eth1  
    inet 192.168.1.1/24 brd 192.168.22.255
    inet 192.168.1.5/32
 
# ipvsadm -Ln
TCP  192.168.22.249:80 rr
  -> 192.168.1.3:80          Masq      1    0    5
  -> 192.168.1.4:80          Masq      1    0    4
```

DR BACKUP：

ip没有变动，为自己原有的ip

```
# ipvsadm -Ln
IP Virtual Server version 1.2.1 (size=4096)
Prot LocalAddress:Port Scheduler Flags
  -> RemoteAddress:Port
```

### **测试**

1，测试Real Server挂掉一个是否影响

把Real Server1的httpd服务关闭，打开VIP页面，一直刷新

2，测试keepalived的MASTER挂掉后，BACKUP能否正常接替主继续工作

把MASTER重启，在重启的期间，一直打开VIP首页查看，MASTER重启后，keepalived开机启动，继续由MASTER提供服务

2016年03月09日 于 [linux工匠](https://bbotte.github.io/) 发表



