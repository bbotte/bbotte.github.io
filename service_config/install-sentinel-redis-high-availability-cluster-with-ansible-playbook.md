# 用ansible-playbook安装redis的sentinel高可用集群

redis的高可用集群方案一般来说分为下面几种,
redis集群 redis cluster <http://www.redis.io/topics/cluster-tutorial> ,
redis哨兵 redis sentinel <http://www.redis.io/topics/sentinel>
keepalived+lvs+redis实现
codis集群 <https://github.com/CodisLabs/codis>

redis sentinel是redis自带的解决方法，轻量并简单，配置方法是: 1，先做一个主从     2，sentinel监控redis主从，如果发现主挂了，提升redis从为主，下面用ansible安装redis

```
# egrep -v "^$|^#" /etc/ansible/hosts
[server]
10.211.55.4 host_name=vm01
10.211.55.5 host_name=vm02
10.211.55.6 host_name=vm03
 
 
# cat /root/ansible/hosts
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
 
10.211.55.4 vm01
10.211.55.5 vm02
10.211.55.6 vm03
```

安装redis的ansible-playbook,获取ipv4 address,更改主机的hostname，解压安装redis，sed修改redis配置，最后启动redis服务

```
#jinja2:  variable_start_string: "[%" , variable_end_string: "%]"
---
  - hosts: server
    remote_user: root
    vars:
      hostname: '[% host_name %]'
      ipv4: '{{ansible_default_ipv4.address}}'
    tasks:
    - name: time sync
      command: ntpdate ntp1.aliyun.com
    - name: copy hosts file
      copy: src=/root/ansible/hosts dest=/etc/hosts owner=root group=root mode=0644 force='yes'
    - name: set hostname
      shell: 'hostname {{host_name}}'
      register: host_name_change
    - debug: msg='{{host_name_change.stdout}}'
    - name: close iptables
      service: name=iptables enabled=yes state=stopped
    - name: copy redis.tar.gz
      copy: src=/root/ansible/redis-3.2.0.tar.gz dest=/tmp/  owner=root group=root mode=0644
    - name: install redis
      shell: cd /tmp/; tar -xzf /tmp/redis-3.2.0.tar.gz; cd /tmp/redis-3.2.0; make -j4; make install
    - name: copy redis.conf to /etc dir
      copy: src=/tmp/redis-3.2.0/redis.conf dest=/etc/ owner=root group=root mode=0644 force='yes'
    - name: copy redis init file to /etc/init.d/
      copy: src=/root/ansible/redis_init.sh dest=/etc/init.d/redis owner=root group=root mode=0755 force='yes'
    - name: mkdir /var/redis
      shell: mkdir -p /var/redis
    - name: change redis config
      shell: sed -i 's/daemonize\ no/daemonize\ yes/g' /etc/redis.conf ; sed -i '/bind 127.0.0.1/d' /etc/redis.conf;echo bind {{ipv4}} 127.0.0.1 >> /etc/redis.conf; sed -i 's/dir\ .\//dir\ \/var\/redis/g' /etc/redis.conf; sed -i 's/appendonly\ no/appendonly\ yes/g' /etc/redis.conf
    - name: start redis service
      service: name=redis enabled=yes state=restarted
    - name: redis status
      shell: echo info |redis-cli |head -n 19
      register: result
    - debug: msg={{result}}
```

redis的启动文件<https://github.com/thinkeverytime/devops2u.com/blob/master/redis_init.sh>

redis已经安装完成并启动了，下面vm01为redis主，vm02为redis从，vm03redis停止，作为sentinel

vm02的/etc/redis.conf 最后添加一行：slaveof 10.211.55.4 6379，并重启，作为vm01的从，从info replication可以获取主从关系的信息,也可以 role 命令查看master、slave、sentinel各个角色的信息

```
root@vm02 ~]# redis-cli -h 10.211.55.5
10.211.55.5:6379> info replication
# Replication
role:slave
master_host:10.211.55.4
master_port:6379
master_link_status:up
master_last_io_seconds_ago:5
master_sync_in_progress:0
slave_repl_offset:29
slave_priority:100
slave_read_only:1
connected_slaves:0
master_repl_offset:0
repl_backlog_active:0
repl_backlog_size:1048576
repl_backlog_first_byte_offset:0
repl_backlog_histlen:0
```

vm03 不用redis服务，启用sentinel

sentinel主要的配置就是下面一行，mymaster为哨兵的名称，后面是redis主的IP，最后面的“1”是因为现在monitor只有1台

sentinel monitor mymaster 10.211.55.4 6379 1

```
root@vm03 ~]# service redis stop
Stopping redis-server:                                     [  OK  ]
[root@vm03 ~]# cp /tmp/redis-3.2.0/sentinel.conf /etc/
[root@vm03 ~]# egrep -v "^$|^#" /etc/sentinel.conf
port 26379
dir /tmp
sentinel monitor mymaster 10.211.55.4 6379 1
sentinel down-after-milliseconds mymaster 30000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 180000
[root@vm03 ~]# redis-sentinel /etc/sentinel.conf &
[1] 20262
[root@vm03 ~]#                 _._
           _.-``__ ''-._
      _.-``    `.  `_.  ''-._           Redis 3.2.0 (00000000/0) 64 bit
  .-`` .-```.  ```\/    _.,_ ''-._
 (    '      ,       .-`  | `,    )     Running in sentinel mode
 |`-._`-...-` __...-.``-._|'` _.-'|     Port: 26379
 |    `-._   `._    /     _.-'    |     PID: 20262
  `-._    `-._  `-./  _.-'    _.-'
 |`-._`-._    `-.__.-'    _.-'_.-'|
 |    `-._`-._        _.-'_.-'    |           http://redis.io
  `-._    `-._`-.__.-'_.-'    _.-'
 |`-._`-._    `-.__.-'    _.-'_.-'|
 |    `-._`-._        _.-'_.-'    |
  `-._    `-._`-.__.-'_.-'    _.-'
      `-._    `-.__.-'    _.-'
          `-._        _.-'
              `-.__.-'
 
20262:X 11 May 15:21:18.437 # Sentinel ID is ea87ab5547e731d11cd95359f414475458e44f87
20262:X 11 May 15:21:18.437 # +monitor master mymaster 10.211.55.4 6379 quorum 1
20262:X 11 May 15:21:18.438 * +slave slave 10.211.55.5:6379 10.211.55.5 6379 @ mymaster 10.211.55.4 6379
```

在redis主随便设置些数据，从肯定是有的，也可以查看/var/redis/redis.log

```
# redis-cli
127.0.0.1:6379> set website devops2u.com
OK
127.0.0.1:6379> get website
"devops2u.com"
```

这时，把vm01的redis主停止，查看redis从和sentinel的变化

redis从状态的转变：

```
[root@vm02 ~]# redis-cli -h 10.211.55.5
10.211.55.5:6379> keys *
1) "website"
10.211.55.5:6379> info replication
# Replication
role:slave
master_host:10.211.55.4
master_port:6379
master_link_status:down
master_last_io_seconds_ago:-1
master_sync_in_progress:0
slave_repl_offset:26781
master_link_down_since_seconds:8
slave_priority:100
slave_read_only:1
connected_slaves:0
master_repl_offset:0
repl_backlog_active:0
repl_backlog_size:1048576
repl_backlog_first_byte_offset:0
repl_backlog_histlen:0
10.211.55.5:6379> info replication
# Replication
role:master
connected_slaves:0
master_repl_offset:0
repl_backlog_active:0
repl_backlog_size:1048576
repl_backlog_first_byte_offset:0
repl_backlog_histlen:0
```

redis sentinel的日志如下：

```
20262:X 11 May 15:28:17.289 # +sdown master mymaster 10.211.55.4 6379
20262:X 11 May 15:28:17.289 # +odown master mymaster 10.211.55.4 6379 #quorum 1/1
20262:X 11 May 15:28:17.289 # +new-epoch 1
20262:X 11 May 15:28:17.289 # +try-failover master mymaster 10.211.55.4 6379
20262:X 11 May 15:28:17.304 # +vote-for-leader ea87ab5547e731d11cd95359f414475458e44f87 1
20262:X 11 May 15:28:17.304 # +elected-leader master mymaster 10.211.55.4 6379
20262:X 11 May 15:28:17.304 # +failover-state-select-slave master mymaster 10.211.55.4 6379
20262:X 11 May 15:28:17.388 # +selected-slave slave 10.211.55.5:6379 10.211.55.5 6379 @ mymaster 10.211.55.4 6379
20262:X 11 May 15:28:17.388 * +failover-state-send-slaveof-noone slave 10.211.55.5:6379 10.211.55.5 6379 @ mymaster 10.211.55.4 6379
20262:X 11 May 15:28:17.455 * +failover-state-wait-promotion slave 10.211.55.5:6379 10.211.55.5 6379 @ mymaster 10.211.55.4 6379
20262:X 11 May 15:28:18.333 # +promoted-slave slave 10.211.55.5:6379 10.211.55.5 6379 @ mymaster 10.211.55.4 6379
20262:X 11 May 15:28:18.333 # +failover-state-reconf-slaves master mymaster 10.211.55.4 6379
20262:X 11 May 15:28:18.419 # +failover-end master mymaster 10.211.55.4 6379
20262:X 11 May 15:28:18.420 # +switch-master mymaster 10.211.55.4 6379 10.211.55.5 6379
20262:X 11 May 15:28:18.420 * +slave slave 10.211.55.4:6379 10.211.55.4 6379 @ mymaster 10.211.55.5 6379
20262:X 11 May 15:28:48.473 # +sdown slave 10.211.55.4:6379 10.211.55.4 6379 @ mymaster 10.211.55.5 6379
```

在转换过程中，或许会提示 READONLY You can’t write against a read only instance，是因为只读的redis实例不能写入数据

redis集群结构已经发生变化，想要修复的话下一步怎么办呢，
1，把vm01的redis配置最后添加 slaveof 10.211.55.5 6379 变为此时redis主的vm02
2，启动vm01的redis，info replication 查看状态

redis-sentinel查看状态:

```
info sentinel
client list
```

现在的结果是vm02为redis主，vm01为redis从，sentinel一样做一个守护神

程序因为一直连接的redis sentinel的ip和port，所以不会出现问题。

如果有多个redis集群，可以用sentinel相互做高可用，sentinel既能相互依存又节省主机，如下图：

```
sentinel_1/sentinel_2      sentinel_2/sentinel_1
          |                        |
  —————————————————      ———————————————————
  |                \   /                    |
  |                  X                      |
  |                /   \                    |
redis1主—————–——–——      —————————————–—–redis2主
  |                                         |
redis1从                                 redis2从
```

2016年05月11日 于 [linux工匠](http://www.bbotte.com/) 发表

