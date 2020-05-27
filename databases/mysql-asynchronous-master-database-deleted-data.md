---
layout: default
---

# Mysql不同步主库删除的数据

**操作要求：**

Mysql中某个库每天产生的数据较大，因为磁盘空间，需要把这个库里面数据清空，并且业务需要对里面的数据做查询。首先想到的是数据库主从，把主库的数据同步到从库，并且主库清空，从库里面数据保留用以查询。用主从只需要同步的时候把delete table 和 truncate table或drop database 命令去掉，不同步删除的数据，只是没有查到相应的软件，所以有下面的操作

**操作思路：**

利用数据库的主从同步，在主数据库执行清除命令，不同步到从数据库

以下主数据库为A(192.168.1.80)，从数据库为B(192.168.1.81)。A里面的gamelog数据库每天清理一次（gamelog数据库，里面一个表 goldenLog），并且在B数据库保留所有的gamelog库信息。假设在晚上23:52  A执行清除mysql数据命令

**实现方法：**

**1，  系统centos 6.4 64位**

**2，  配置mysql 5.5.37 主从同步，过程略过**

**3，  23:50 A中刷新日志** 为的是接下来进行处理的日志较小，更方便的修改，导入到从服务器

```
/usr/local/mysql/bin/mysql -e "flush binarylogs;   show master status\G"|grep -E "File|Position" |\
awk '{print $2}'
mysql-bin.000023   107
```

**4，  23:51  B中停止同步，并且记录position**

```
/usr/local/mysql/bin/mysql -e "stop slave;  show slavestatus\G" |grep -E "Master_Log_File|\
Read_Master_Log_Pos" |awk'{print $2}'|awk 'NR < 3'
mysql-bin.000023    196
```

**5，  23:52  A中保留表结构，清除表中的内容**

```
/usr/local/mysql/bin/mysql -e "show master status\G"|grep -E "File|Position"|\
awk '{print $2}'  > sqlstatus | /usr/local/mysql/bin/mysql -nse 'show tables' gamelog|\
while read table;do /usr/local/mysql/bin/mysql -e "truncate table $table" gamelog;done
```

查看现在的Position位置 

```
cat sqlstatus
mysql-bin.000023
1136417
```

清理数据后执行刷新log，从服务器同步就从刷新后日志position的107开始向主请求同步

```
/usr/local/mysql/bin/mysql -e "flush binary logs;   show master status\G"|\
grep -E "File|Position"|awk '{print $2}'|sed -n 1p
B同步A中的内容就利用这个位置 
mysql-bin.000024
```

**6，  A中把二进制日志导出为sql命令并发送给从**

```
/usr/local/mysql/bin/mysqlbinlog mysql-bin.000023 > 000023.sql
```

下面是清空数据库里面表内容的命令，需要把这一条语句给删除，然后发送给从服务器

```
#at 1136417
#14061016:22:45 server id 1  end_log_pos 1136417       Query  \
#               thread_id=22 exec_time=0     error_code=0
SETTIMESTAMP=1402388565/*!*/;
truncate table goldenLog
/*!*/;
```

```
grep -rn "end_log_pos 1136417" 000023.sql |cut -d: -f1
51502
sed -i 51503,51505d 000023.sql
```

把修改的sql传到B  这里需要配置双机互信，具体过程略过

```
scp 000023.sql 192.168.1.81:/root/
```

**7，  B中 mysql 导入数据** 000023.sql 此时导入的数据没有清空表内容的命令，所以内容就不会被删除

```
/usr/local/mysql/bin/mysql  <<EOF
> source/root/000023.sql;
>EOF
```

**8，  B 开始向A请求同步  **mysql-bin日志为（上面第五条5，）A执行刷新log后的bin log

```
/usr/local/mysql/bin/mysql-e "change master to master_log_file='mysql-bin.000024',master_log_pos=107;"
```

**9， B中 开始恢复主从同步**

```
/usr/local/mysql/bin/mysql -e "slave start;"
```

查看B中状态

```
/usr/local/mysql/bin/mysql -e "show slavestatus\G " | grep -E "Slave_IO_Running|\
Slave_SQL_Running" |awk'{print $2}'
```

**改写脚本：**

**A中脚本：**

```
#!/bin/bash
#crontab
#50 23 * * * sh /root/master.sh
 
mysqlbin_num=`/usr/local/mysql/bin/mysql -e "flush binary logs; show master status\G"|\
grep -E "File|Position" |awk '{print $2}'|grep mysql-bin |cut -d\. -f2`
sleep 10
/usr/local/mysql/bin/mysql -e "show master status\G"|grep -E "File|Position"|\
awk '{print $2}' > sqlstatus|/usr/local/mysql/bin/mysql -nse 'show tables' gamelog|\
while read table;do /usr/local/mysql/bin/mysql -e "truncate table $table" gamelog;done
 
/usr/local/mysql/bin/mysql -e "flush binary logs;   show masterstatus\G"|\
grep -E "File|Position"|awk '{print $2}'|sed -n 1p
 
/usr/local/mysql/bin/mysqlbinlog /var/mysql/log/mysql-bin.${mysqlbin_num} > \
/root/${mysqlbin_num}.sql
line=`grep -n "truncate table goldenLog" /root/${mysqlbin_num}.sql|cut -d: -f1`
line1=$((${line}-3))
line2=$((${line}+1))
sed -i ${line1},${line2}d /root/${mysqlbin_num}.sql
 
scp /root/${mysqlbin_num}.sql 192.168.1.81:/root/
```

**B中脚本：**

```
#!/bin/bash
#crontab
#50 23 * * * sh /root/slave.sh
sleep 5
/usr/local/mysql/bin/mysql -e "stop slave;  show slavestatus\G"|\
grep -E "Master_Log_File|Read_Master_Log_Pos" |awk 'NR< 3'
 
sleep 20
 
sqlbin_num=`find /root/*.sql|cut -d\/ -f3|cut -d. -f1|sort -n|tail -n 1`
 
/usr/local/mysql/bin/mysql <<EOF
source /root/${sqlbin_num}.sql;
EOF
 
mysqllog_num=`/usr/local/mysql/bin/mysql -e "show slave status\G" |\
grep -E "Master_Log_File|Read_Master_Log_Pos" |awk '{print $2}'|awk 'NR <3' |\
grep mysql-bin |cut -d. -f2 |perl -pe 's/\b0+//g'`
sql_num=$((${mysqllog_num}+1))
mysqllog=`printf %06d ${sql_num}`
 
sleep5
 
/usr/local/mysql/bin/mysql -e "change master to master_log_file='mysql-bin.${mysqllog}',master_log_pos=107;"
 
/usr/local/mysql/bin/mysql -e "slave start;"
```

2016年03月14日 于 [linux工匠](https://bbotte.github.io/) 发表