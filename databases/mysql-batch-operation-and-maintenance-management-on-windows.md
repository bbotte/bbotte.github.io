---
layout: default
---

# windows主机对Mysql批量运维管理

Windows主机上跑了一个mysql服务，因为没有bash命令行，仅适用cmd命令太麻烦，于是安装Git Bash <https://gitforwindows.org/> 带有linux内核的git操作软件。于是乎，所有的操作步骤变为和linux环境相似。

当然，以下mysql的操作在linux下一样执行。当前mysql有多个库，每个库包含多张表

1.查看当前所有数据库

```
/c/Program\ Files/MySQL/MySQL\ Server\ 5.7/bin/mysql.exe -uroot -p123456 -e "show databases\G"|grep Database|awk '{print $2}'  |egrep -w -v "information_schema|mysql|percona|performance_schema|sys" > dbname
```

2.按数据库备份数据（结构和数据）

```
cat dbname|while read i ;do /c/Program\ Files/MySQL/MySQL\ Server\ 5.7/bin/mysqldump.exe -uroot -p123456 $i >> /e/mysqlback/$i.sql ;done
```

3.备份总数据库

```
CurrentTime=`date +%F_%H-%M-%S`
/c/Program\ Files/MySQL/MySQL\ Server\ 5.7/bin/mysqldump -uroot -p123456 --single-transaction --default-character-set=utf8 --all-databases --set-gtid-purged=OFF --triggers --routines --events > /e/mysqlback/dbbackup-${CurrentTime}.sql
```

4.获取当前所有表名称

```
cat dbname|while read i;do /c/Program\ Files/MySQL/MySQL\ Server\ 5.7/bin/mysql.exe -uroot -p123456 -e "use ${i};select TABLE_SCHEMA,table_name from information_schema.tables where table_schema='${i}' and table_type='base table';"|awk 'NR>1{print $1"."$2}' >> ./table_name ;done
```

5.对表名称转码

```
dos2unix.exe table_name
```

6.仅备份数据，不备份数据结构

```
cat table_name|while read i;do /c/Program\ Files/MySQL/MySQL\ Server\ 5.7/bin/mysqldump.exe -uroot -p123456 -c -t `echo $i|awk -F'.' '{print $1}'` `echo $i|awk -F'.' '{print $2}'` > $i.sql;done
```

7.创建数据库

```
cat dbname|while read i ;do /c/Program\ Files/MySQL/MySQL\ Server\ 5.7/bin/mysql.exe -uroot -p123456 -e "create schema $i default CHARACTER set utf8 COLLATE utf8_general_ci;";done
```

8.导入当前文件夹数据到相应数据库

```
ls *.*.sql|while read i ;do /c/Program\ Files/MySQL/MySQL\ Server\ 5.7/bin/mysql.exe -uroot -p123456 --default-character-set=utf8 -e "use `echo $i|awk -F'.' '{print $1}'`;source d:/dbbak2019/$i;";done
```

9.在git bash登录数据库

```
winpty /c/Program\ Files/MySQL/MySQL\ Server\ 5.7/bin/mysql.exe -uroot -p123456
```

以上步骤可满足数据库环境不一致，大版本更新等

2019年03月25日 于 [linux工匠](https://bbotte.github.io/) 发表