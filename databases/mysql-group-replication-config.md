---
layout: default
---

# mysql组复制mysql group replication配置

mgr和proxysql更配哦

### mysql组复制配置

配置文档见
<https://github.com/bbotte/bbotte.com/tree/master/service/mysql-mgr>

mysql group replication所需条件
1.只能为innodb引擎
2.所有表必须有主键
其他限制请看官方文档

my.cnf配置添加如下，下面为mgr单主模式

```
[mysqld]
read_only=1
disabled_storage_engines="BLACKHOLE,FEDERATED,ARCHIVE,MEMORY"
plugin_load_add='group_replication.so'
transaction_write_set_extraction=XXHASH64
loose-group_replication_group_name="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
loose-group_replication_start_on_boot=off
loose-group_replication_bootstrap_group=off
loose-group_replication_local_address="172.17.1.10:3317"
loose-group_replication_group_seeds="172.17.1.10:3317,172.17.1.20:3327,172.17.1.30:3337"
 
server_id=1
gtid_mode=ON
enforce_gtid_consistency=ON
master_info_repository=TABLE
relay_log_info_repository=TABLE
binlog_checksum=NONE
log_slave_updates=ON
log_bin=binlog
binlog_format=ROW
```

不同节点，group_replication_local_address、server_id 不同，需要更改

配置完成后，启动3个mysql实例，并在所有库执行

```
SET SQL_LOG_BIN=0;
CREATE USER irisrepluser@'%' IDENTIFIED BY '123456';
GRANT REPLICATION SLAVE ON *.* TO irisrepluser@'%';
FLUSH PRIVILEGES;
SET SQL_LOG_BIN=1;
CHANGE MASTER TO MASTER_USER='irisrepluser', MASTER_PASSWORD='123456' FOR CHANNEL 'group_replication_recovery';
```

主库执行

```
SET GLOBAL group_replication_bootstrap_group=ON;
START GROUP_REPLICATION;
SET GLOBAL group_replication_bootstrap_group=OFF;
SELECT * FROM performance_schema.replication_group_members;
```

2个备库执行

```
set global group_replication_allow_local_disjoint_gtids_join=ON;
START GROUP_REPLICATION;
```

一般来说，现在3个mysql节点状态都为ONLINE

常用命令

```
SELECT * FROM performance_schema.replication_group_members;
show global variables like '%read_only%';
SELECT * FROM performance_schema.replication_group_member_stats\G
SELECT * FROM performance_schema.replication_applier_status\G
SELECT * FROM performance_schema.replication_connection_status\G
SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'group_replication_primary_member';
SELECT MEMBER_ID, MEMBER_HOST,MEMBER_PORT,MEMBER_STATE,IF(global_status.VARIABLE_NAME IS NOT NULL,'PRIMARY','SECONDARY') AS MEMBER_ROLE FROM performance_schema.replication_group_members LEFT JOIN performance_schema.global_status ON global_status.VARIABLE_NAME = 'group_replication_primary_member' AND global_status.VARIABLE_VALUE = replication_group_members.MEMBER_ID;
show global variables like '%group_replication%';
```

### mgr状态错误

1.加载group_replication.so出错

```
INSTALL PLUGIN group_replication SONAME 'group_replication.so';
ERROR 1030 (HY000): Got error 1 from storage engine
```

my.cnf配置中添加 plugin_load_add=’group_replication.so’

```
show plugins;
```

2.mysql在docker中启动组复制不能启动

```
START GROUP_REPLICATION;
ERROR 3096 (HY000): The START GROUP_REPLICATION command failed as there was an error when initializing the group communication layer.
[Note] Plugin group_replication reported: 'Requesting to leave the group despite of not being a member'
```

<https://bugs.mysql.com/bug.php?id=86772>

用新版本mysql解决问题

3.由于allow_local_disjoint_gtids_join关闭状态MEMBER_STATE为RECOVERING

```
mysql> START GROUP_REPLICATION;
ERROR 3092 (HY000): The server is not configured properly to be an active member of the group. Please see more details on error log.
mysql> set global group_replication_allow_local_disjoint_gtids_join=ON;
mysql> START GROUP_REPLICATION;
```

4.由于从库同步点问题MEMBER_STATE为RECOVERING

```
SELECT * FROM performance_schema.replication_group_members;
```

状态是RECOVERING

现在2个从库状态是RECOVERING，状态有问题，查日志

```
[ERROR] Slave SQL for channel 'group_replication_recovery': Worker 1 failed executing transaction 'b3b803ed-b358-11e9-85c2-0242ac11010a:1' at master log mysql-bin.000002, end_log_pos 369; Could not execute Write_rows event on table mysql.time_zone; Duplicate entry '1' for key 'PRIMARY', Error_code: 1062; handler error HA_ERR_FOUND_DUPP_KEY; the event's master log FIRST, end_log_pos 369, Error_code: 1062
```

那么就跳过这个错误，查看主库已经执行的gtid，因为数据库是刚初始化的，所以gtid_purged为空，如果gtid_purged有值的话，就跳过gtid_purged的值。即确保数据一致的情况下开始主从同步
主库查看现在执行过的gtid值：

```
show global variables like 'gtid_executed';
```

从库执行：

```
STOP GROUP_REPLICATION;
reset master;
set global gtid_purged = 'b3b803ed-b358-11e9-85c2-0242ac11010a:1';
START GROUP_REPLICATION;
SELECT * FROM performance_schema.replication_group_members;
```

现在3个数据库状态都为ONLINE

5.由于hosts问题MEMBER_STATE为RECOVERING

```
[ERROR] Plugin group_replication reported: 'There was an error when connecting to the donor server. Please check that group_replication_recovery channel credentials and all MEMBER_HOST column values of performance_schema.replication_group_members table are correct and DNS resolvable.'
[ERROR] Plugin group_replication reported: 'For details please check performance_schema.replication_connection_status table and error log messages of Slave I/O for channel group_replication_recovery.'
```

如果是上面的报错，那么绑定hosts，把ip和主机名绑定，MEMBER_STATE的RECOVERING状态自然就变为ONLINE

6.由于主库没有创建同步账号irisrepluser导致不能同步数据

```
[ERROR] Plugin group_replication reported: 'There was an error when connecting to the donor server
. Please check that group_replication_recovery channel credentials and all MEMBER_HOST column values of performance_schema.replication_
group_members table are correct and DNS resolvable.'
[ERROR] Plugin group_replication reported: 'For details please check performance_schema.replicatio
n_connection_status table and error log messages of Slave I/O for channel group_replication_recovery.'
```

7.数据库没有reset master导致日志有错误提示，可忽略

```
[ERROR] Plugin group_replication reported: 'This member has more executed transactions than those present in the group. Local transactions:  Group transactions:
```

### 线上数据库在mgr的操作

mysql: 5.7.21

数据导入主节点，其他节点数据自动同步

线上数据库备份脚本如下：

```
#!/bin/bash
mysql -p123456 -e "show databases;"|grep -Ev "information_schema|mysql|Database|sys|performance_schema" |xargs mysqldump -p123456 -uroot --single-transaction --default-character-set=utf8 --master-data=1 --databases --triggers --routines --events > all.sql
```

```
sed -i '1,20s#SET @@SESSION.SQL_LOG_BIN= 0;#SET @@SESSION.SQL_LOG_BIN= 1;#' all.sql
```

默认全库备份导入时不生成二进制日志，要修改导入数据生成二进制日志

在写节点导入线上数据库备份

```
source /root/all.sql;
```

现在3个mysql节点MEMBER_STATE均为ONLINE

\~~~~~~~~~~~

更改3台mysql配置文件

```
vim /etc/my.cnf
loose-group_replication_allow_local_disjoint_gtids_join=on
loose-group_replication_start_on_boot=on
```

这样3个mysql节点其中一台重启，集群不受影响

参考
<https://dev.mysql.com/doc/refman/5.7/en/group-replication.html>

2019年08月13日 于 [linux工匠](http://www.bbotte.com/) 发表