---
layout: default
---

# Mysql数据库引擎innodb转换为TokuDB

一，先安装带有tokudb引擎的mariadb数据库
二，调整内存使用的比率及删除外键
三，生成转换tokudb的脚本
四，更改tokudb的参数

### 说明

阿里云mysql数据库innodb引擎转换为tokudb

TokuDB是一个高性能、写密集型引擎，提供了更高的压缩和更好的性能 The TokuDB storage engine is for use in high-performance and write-intensive environments, offering increased compression and better performance.

使用须知
1、 TokuDB可以大幅度降低存储使用量和IOPS开销
2、 TokuDB支持在线DDL，添加/删除列和索引不会引起阻塞
3、 TokuDB无法支持外键Foreign Key
4、 TokuDB不适用于大量读取的场景

### **一，先安装带有tokudb引擎的mariadb数据库**

install mariadb

```
# cat /etc/centos-release
CentOS release 6.7 (Final)
# vim /etc/yum.repos.d/mariadb.repo
# MariaDB 5.5 CentOS repository list - created 2013-08-11 14:22 UTC
# http://mariadb.org/mariadb/repositories/
[mariadb]
name = MariaDB
baseurl = http://yum.mariadb.org/5.5/centos6-amd64
gpgkey=https://yum.mariadb.org/RPM-GPG-KEY-MariaDB
gpgcheck=1
 
# yum -y install MariaDB
Server version: 5.5.50-MariaDB MariaDB Server
 
或者在此网站下载mariadb安装包
http://archive.mariadb.org/
```

tokudb引擎依赖ha_tokudb.so，此模块在/usr/lib64/mysql/plugin/ha_tokudb.so，因此初始化mysql：

```
/usr/bin/mysql_install_db --user=mysql  --datadir=/var/mysql/data --basedir=/usr --log-output=file --plugin-dir=/usr/lib64/mysql/plugin/ --log-error=/var/log/mysql/mysql-error.log --pid-file=/var/log/mysql/mysql.pid --socket=/var/lib/mysql/mysql.sock --defaults-file=/etc/my.cnf
```

centos系统参数调整：

```
echo never > /sys/kernel/mm/redhat_transparent_hugepage/defrag
echo never > /sys/kernel/mm/redhat_transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
```

启动mysql查看默认参数：

```
# service mysql start
Starting MySQL.. SUCCESS!
# mysql
Welcome to the MariaDB monitor.  Commands end with ; or \g.
Your MariaDB connection id is 3
Server version: 5.5.50-MariaDB MariaDB Server
 
Copyright (c) 2000, 2016, Oracle, MariaDB Corporation Ab and others.
 
Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.
MariaDB [(none)]> SHOW VARIABLES LIKE 'tokudb_version'\G
*************************** 1. row ***************************
Variable_name: tokudb_version
Value: tokudb-7.5.7
 
MariaDB [(none)]> SHOW VARIABLES LIKE '%tokudb%';
+---------------------------------+--------------+
| Variable_name                   | Value        |
+---------------------------------+--------------+
| tokudb_alter_print_error        | OFF          |
| tokudb_analyze_delete_fraction  | 1.000000     |
| tokudb_analyze_time             | 5            |
| tokudb_block_size               | 4194304      |
| tokudb_bulk_fetch               | ON           |
| tokudb_cache_size               | 134217728    |
| tokudb_check_jemalloc           | 1            |
| tokudb_checkpoint_lock          | OFF          |
| tokudb_checkpoint_on_flush_logs | OFF          |
| tokudb_checkpointing_period     | 60           |
| tokudb_cleaner_iterations       | 5            |
| tokudb_cleaner_period           | 1            |
| tokudb_commit_sync              | ON           |
| tokudb_create_index_online      | ON           |
| tokudb_data_dir                 |              |
| tokudb_debug                    | 0            |
| tokudb_directio                 | OFF          |
| tokudb_disable_hot_alter        | OFF          |
| tokudb_disable_prefetching      | OFF          |
| tokudb_disable_slow_alter       | OFF          |
| tokudb_empty_scan               | rl           |
| tokudb_fs_reserve_percent       | 5            |
| tokudb_fsync_log_period         | 0            |
| tokudb_hide_default_row_format  | ON           |
| tokudb_killed_time              | 4000         |
| tokudb_last_lock_timeout        |              |
| tokudb_load_save_space          | ON           |
| tokudb_loader_memory_size       | 100000000    |
| tokudb_lock_timeout             | 4000         |
| tokudb_lock_timeout_debug       | 1            |
| tokudb_log_dir                  |              |
| tokudb_max_lock_memory          | 16777216     |
| tokudb_optimize_index_fraction  | 1.000000     |
| tokudb_optimize_index_name      |              |
| tokudb_optimize_throttle        | 0            |
| tokudb_pk_insert_mode           | 1            |
| tokudb_prelock_empty            | ON           |
| tokudb_read_block_size          | 65536        |
| tokudb_read_buf_size            | 131072       |
| tokudb_read_status_frequency    | 10000        |
| tokudb_row_format               | tokudb_zlib  |
| tokudb_rpl_check_readonly       | ON           |
| tokudb_rpl_lookup_rows          | ON           |
| tokudb_rpl_lookup_rows_delay    | 0            |
| tokudb_rpl_unique_checks        | ON           |
| tokudb_rpl_unique_checks_delay  | 0            |
| tokudb_support_xa               | ON           |
| tokudb_tmp_dir                  |              |
| tokudb_version                  | tokudb-7.5.7 |
| tokudb_write_status_frequency   | 1000         |
+---------------------------------+--------------+
50 rows in set (0.00 sec)
 
MariaDB [(none)]> show engine tokudb status;
```

参数设置参考
<https://mariadb.com/kb/en/mariadb/tokudb-system-variables/>
<https://www.percona.com/doc/percona-server/5.7/tokudb/tokudb_variables.html>

### **二，调整内存使用的比率及删除外键**

1,阿里云的rds数据库服务器，有loose_tokudb_buffer_pool_ratio这个参数，如果数据库由innodb或者myisam转为tokudb，需要调整内存的使用比率，下面为阿里云rds的调整：

设置loose_tokudb_buffer_pool_ratio为合适的比例，也就是tokudb占用tokudb与innodb共用缓存的比例，默认在tokudb不使用的情况下是0，如果全部都用tokudb可以改为100，也可以在innodb转换tokudb前根据下面公式来计算：

```
select sum(data_length) into @all_size from information_schema.tables where engine='innodb';
select sum(data_length) into @change_size from information_schema.tables where engine='innodb' and concat(table_schema, '.', table_name) in ('XX.XXXX', 'XX.XXXX', 'XX.XXXX');
select round(@change_size/@all_size*100);
 
举个例子说明：
select sum(data_length) into @innodb_size from information_schema.tables where engine='innodb';
select sum(data_length) into @change_size from information_schema.tables where engine='innodb' and concat(table_schema, '.', table_name) in ('databasename.tablename');
select round(@tokudb_size/(@innodb_size+@tokudb_size)*100);
```

更改完这个参数后再开始转换引擎，如果是一个新的数据库，此步骤忽略

2,mariadb没有loose_tokudb_buffer_pool_ratio参数，我们可以修改配置文件，如下操作，参数根据实际情况设置：

```
# egrep -v "^$|^#" /etc/my.cnf
[client-server]
!includedir /etc/my.cnf.d
 
# egrep -v "^$|^#" /etc/my.cnf.d/server.cnf
[server]
innodb_buffer_pool_size = 512M
[mysqld]
[embedded]
[mysqld-5.5]
[mariadb]
[mariadb-5.5]
 
# egrep -v "^$|^#" /etc/my.cnf.d/tokudb.cnf
[mariadb]
tokudb_cache_size=512M
```

3，因为tokudb不支持外键，所以转换引擎之前删除

```
echo "SELECT CONCAT('ALTER TABLE ',table_schema,'.',table_name,' DROP FOREIGN KEY ',constraint_name,';') FROM information_schema.table_constraints WHERE CONSTRAINT_TYPE = 'FOREIGN KEY' AND CONSTRAINT_SCHEMA LIKE 'prefix_of_my_tables_%'" | mysql ${MYSQL_CONN} | grep -v CONCAT > drop_all_foreign.sql
```

### **三，生成转换tokudb的脚本**

1，直接生成alter的语句，用screen后台执行

```
MYSQL_USER=bbotte
MYSQL_PASS=bbotte.com
MYSQL_PORT=3306
MYSQL_HOST=127.0.0.1
MYSQL_CONN=" -u${MYSQL_USER} -p${MYSQL_PASS} -h${MYSQL_HOST} -P${MYSQL_PORT}"
SQLSTMT="SELECT CONCAT('mysql ${MYSQL_CONN} -e\"ALTER TABLE ',table_schema,'.', table_name,' ENGINE=TokuDB;\"') InnoDBConversionSQL FROM information_schema.tables WHERE engine='InnoDB' ORDER BY data_length"
mysql ${MYSQL_CONN} -e"${SQLSTMT}" >> tokudb.sh
```

2，如果用percona-toolkit的话，可以这样生成：

```
wget https://www.percona.com/downloads/percona-toolkit/2.2.18/deb/percona-toolkit_2.2.18-1.tar.gz
tar -xzf percona-toolkit_2.2.18-1.tar.gz
cd percona-toolkit-2.2.18/
yum install perl-DBD-MySQL perl-Time-HiRes
perl Makefile.PL
make
make install
pt-online-schema-change -h
```

下面为生成的shell

```
MYSQL_USER=bbotte
MYSQL_PASS=bbotte.com
MYSQL_PORT=3306
MYSQL_HOST=127.0.0.1
MYSQL_CONN=" -u${MYSQL_USER} -p${MYSQL_PASS} -h${MYSQL_HOST} -P${MYSQL_PORT}"
SQLSTMT="SELECT CONCAT('pt-online-schema-change ','${MYSQL_CONN}',' --no-version-check --execute --alter ','\"ENGINE=TokuDB\"',' D=',table_schema,',t=',table_name,' --recursion-method=none --no-check-replication-filters --quiet --critical-load=\"Threads_running=300\" ') InnoDBConversionSQL FROM information_schema.tables WHERE engine='InnoDB' ORDER BY data_length"
mysql ${MYSQL_CONN} -e"${SQLSTMT}" >> pt-tokudb.sh
```

还有几个参数对tokudb的转换速度影响较大
tokudb_cache_size: Size in bytes of the TokuDB cache，相当于innodb的innodb_buffer_pool_size
tokudb_load_save_space : default is off and should be left alone unless you are low on disk space.
tokudb_cache_size : if unset the TokuDB will allocate 50% of RAM for it’s own caching mechanism, we generally recommend leaving this setting alone. As you are running on an existing server you need to make sure that you aren’t over-committing memory between TokuDB, InnoDB, and MyISAM.

### **四，更改tokudb的参数**

1，更改默认db引擎
set global default_storage_engine=TokuDB;

2，更改tokudb的使用内存
loose_tokudb_buffer_pool_ratio=100(阿里云rds)
tokudb_cache_size=物理内存的60%

转换完成后，数据库的占用空间是以前的30%，压缩效果挺大的，更多信息请持续关注。

可以参考的资料：

[MariaDB的tokudb介绍](https://mariadb.com/kb/en/mariadb/tokudb/)
[percona的tokudb引擎介绍](https://github.com/percona/tokudb-engine)
[RDS TokuDB小手册](http://mysql.taobao.org/monthly/2015/04/02/)
[RDS MySQL空间优化最佳实践](https://yq.aliyun.com/articles/55594)
[Percona TokuDB – Documentation](https://www.percona.com/doc/percona-tokudb/index.html)

2016年07月16日 于 [linux工匠](https://bbotte.github.io/) 发表