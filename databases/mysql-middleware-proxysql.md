---
layout: default
---

# mysql中间件proxysql

主库鸭梨大，需要做主从分离，现在数据库结构为mha，添加mysql主从分离中间件

几个mysql中间件对比后

MariaDB的MaxScale：不支持跨库子查询，pass

360的Atlas：文档少，现在也没更新了，issus没回复

proxysql：分离规则灵活，在线修改配置

 

proxy作用：主从分离，管理节点的权重，连接配置等。可以根据 数据库登录用户名、匹配规则、连接权重 等路由mysql语句，是一个很灵活的中间件

mysql MHA的作用：主节点切换，同步故障后的binlog，让主备节点可写

mysql主备、mysql从库需要设置  **set global read_only=1;**  ProxySQL monitor模块会监控hostgroups
后端所有servers 的read_only 变量，如果发现从库的read_only变为0、主库变为1，则认为角色互换了，自动改写mysql_servers表里面 hostgroup关系，达到自动 Failover 效果，所以不能写的数据库要设置这个参数

```
              app
               |
           keepalived
          /        \
   proxysql          proxysql
         \             / 
             \     /
                X
             /     \
                |
       /        |        \
mysql主主   mysql主备    mysql从库
   0.10       0.20         0.30
     \          |          /
            mysql MHA
```

安装：

<https://github.com/sysown/proxysql/releases> 下载最新版的rpm安装即可，我装的proxysql-1.4.14-1.1.el7.x86_64.rpm

配置：

```
# cat /etc/proxysql.cnf
#file proxysql.cfg
 
########################################################################################
# This config file is parsed using libconfig , and its grammar is described in:        
# http://www.hyperrealm.com/libconfig/libconfig_manual.html#Configuration-File-Grammar 
# Grammar is also copied at the end of this file                                       
########################################################################################
 
########################################################################################
# IMPORTANT INFORMATION REGARDING THIS CONFIGURATION FILE:                             
########################################################################################
# On startup, ProxySQL reads its config file (if present) to determine its datadir. 
# What happens next depends on if the database file (disk) is present in the defined
# datadir (i.e. "/var/lib/proxysql/proxysql.db").
#
# If the database file is found, ProxySQL initializes its in-memory configuration from 
# the persisted on-disk database. So, disk configuration gets loaded into memory and 
# then propagated towards the runtime configuration. 
#
# If the database file is not found and a config file exists, the config file is parsed 
# and its content is loaded into the in-memory database, to then be both saved on-disk 
# database and loaded at runtime.
#
# IMPORTANT: If a database file is found, the config file is NOT parsed. In this case
#            ProxySQL initializes its in-memory configuration from the persisted on-disk
#            database ONLY. In other words, the configuration found in the proxysql.cnf
#            file is only used to initial the on-disk database read on the first startup.
#
# In order to FORCE a re-initialise of the on-disk database from the configuration file 
# the ProxySQL service should be started with "service proxysql initial".
#
########################################################################################
 
datadir="/var/lib/proxysql"   #配置存放文件夹
 
admin_variables=                    #管理端配置
{
	admin_credentials="admin:admin"            #管理端用户名密码
#	mysql_ifaces="127.0.0.1:6032;/tmp/proxysql_admin.sock"
	mysql_ifaces="0.0.0.0:6032"                #管理端端口
#	refresh_interval=2000
#	debug=true
}
 
mysql_variables=
{
	threads=10                      #开多少线程
	max_connections=2048            #最大连接数
	default_query_delay=0
	default_query_timeout=36000000
	have_compress=true
	poll_timeout=2000
#	interfaces="0.0.0.0:6033;/tmp/proxysql.sock"
	interfaces="0.0.0.0:3306"      #代理的外部端口，就是服务连接mysql中间件的端口
	default_schema="information_schema"  #默认连接数据库
	stacksize=1048576
	server_version="5.7.20"          #数据库版本号
	connect_timeout_server=3000
# make sure to configure monitor username and password
# https://github.com/sysown/proxysql/wiki/Global-variables#mysql-monitor_username-mysql-monitor_password
	monitor_username="monitor"            #检查主从一致性的用户名密码，需要mysql grant授权
	monitor_password="monitor"
	monitor_history=600000
	monitor_connect_interval=60000
	monitor_ping_interval=10000
	monitor_read_only_interval=1500
	monitor_read_only_timeout=500
	ping_interval_server_msec=120000
	ping_timeout_server=500
	commands_stats=true
	sessions_sort=true
	connect_retries_on_failure=10
}
 
 
# defines all the MySQL servers
mysql_servers =                     #添加数据库，mysql主主、mysql主备、mysql从库
(
{
address = "172.16.0.10"             #mysql主主的IP，不是MHA VIP
port = 3306
hostgroup = 0
status = "ONLINE"
weight = 1
},
{
address = "172.16.0.20"
port = 3306
hostgroup = 1
status = "ONLINE"
weight = 2
},
{
address = "172.16.0.30"
port = 3306
hostgroup = 1
status = "ONLINE"
weight = 1
}
#	{
#		address = "127.0.0.1" # no default, required . If port is 0 , address is interpred as a Unix Socket Domain
#		port = 3306           # no default, required . If port is 0 , address is interpred as a Unix Socket Domain
#		hostgroup = 0	        # no default, required
#		status = "ONLINE"     # default: ONLINE
#		weight = 1            # default: 1
#		compression = 0       # default: 0
#   max_replication_lag = 10  # default 0 . If greater than 0 and replication lag passes such threshold, the server is shunned
#	},
#	{
#		address = "/var/lib/mysql/mysql.sock"
#		port = 0
#		hostgroup = 0
#	},
#	{
#		address="127.0.0.1"
#		port=21891
#		hostgroup=0
#		max_connections=200
#	},
#	{ address="127.0.0.2" , port=3306 , hostgroup=0, max_connections=5 },
#	{ address="127.0.0.1" , port=21892 , hostgroup=1 },
#	{ address="127.0.0.1" , port=21893 , hostgroup=1 }
#	{ address="127.0.0.2" , port=3306 , hostgroup=1 },
#	{ address="127.0.0.3" , port=3306 , hostgroup=1 },
#	{ address="127.0.0.4" , port=3306 , hostgroup=1 },
#	{ address="/var/lib/mysql/mysql.sock" , port=0 , hostgroup=1 }
)
 
# defines all the MySQL users
mysql_users:
(
{
username = "root"                     #mysql可写的用户名密码,默认组为0
password = "123456"
active = 1
default_hostgroup = 0
max_connections = 1000
},
{                                    #mysql读的用户名密码
username = "readuser"
password = "654321"
active = 1
default_hostgroup = 1
max_connections = 1000
},
{                                    #mysql某一个库可写的用户名密码，默认组为0，如果是insert或update，
username = "system"                  #会到hostgroup =0 里面，如果是select查询回到 hostgroup =1里面
password = "system"
active = 1
default_hostgroup = 0
max_connections = 1000
}
#}
#	{
#		username = "username" # no default , required
#		password = "password" # default: ''
#		default_hostgroup = 0 # default: 0
#		active = 1            # default: 1
#	},
#	{
#		username = "root"
#		password = ""
#		default_hostgroup = 0
#		max_connections=1000
#		default_schema="test"
#		active = 1
#	},
#	{ username = "user1" , password = "password" , default_hostgroup = 0 , active = 0 }
)
 
#defines MySQL Query Rules
mysql_query_rules:
(
{
rule_id = 1
active = 1
match_pattern="^delete"
destination_hostgroup=0
apply=1
},
{
rule_id = 2
active = 1
match_pattern="^INSERT"
destination_hostgroup=0
apply=1
},
{
rule_id = 3
active = 1
match_pattern="^UPDATE"
destination_hostgroup=0
apply=1
},
{
rule_id = 4
active = 1
match_pattern="^SELECT .* FOR UPDATE$"
destination_hostgroup=0
apply=1
},
{
rule_id = 5
active = 1
match_pattern="^SELECT"
destination_hostgroup=1
apply=1
}
 
#	{
#		rule_id=1
#		active=1
#		match_pattern="^SELECT .* FOR UPDATE$"
#		destination_hostgroup=0
#		apply=1
#	},
#	{
#		rule_id=2
#		active=1
#		match_pattern="^SELECT"
#		destination_hostgroup=1
#		apply=1
#	}
)
 
scheduler=
(
#  {
#    id=1
#    active=0
#    interval_ms=10000
#    filename="/var/lib/proxysql/proxysql_galera_checker.sh"
#    arg1="0"
#    arg2="0"
#    arg3="0"
#    arg4="1"
#    arg5="/var/lib/proxysql/proxysql_galera_checker.log"
#  }
)
 
 
mysql_replication_hostgroups=
(
{
writer_hostgroup=0
reader_hostgroup=1
}
#        {
#                writer_hostgroup=30
#                reader_hostgroup=40
#                comment="test repl 1"
#       },
#       {
#                writer_hostgroup=50
#                reader_hostgroup=60
#                comment="test repl 2"
#        }
)
 
 
# http://www.hyperrealm.com/libconfig/libconfig_manual.html#Configuration-File-Grammar
#
# Below is the BNF grammar for configuration files. Comments and include directives are not part of the grammar, so they are not included here. 
#
# configuration = setting-list | empty
#
# setting-list = setting | setting-list setting
#     
# setting = name (":" | "=") value (";" | "," | empty)
#     
# value = scalar-value | array | list | group
#     
# value-list = value | value-list "," value
#     
# scalar-value = boolean | integer | integer64 | hex | hex64 | float
#                | string
#     
# scalar-value-list = scalar-value | scalar-value-list "," scalar-value
#     
# array = "[" (scalar-value-list | empty) "]"
#     
# list = "(" (value-list | empty) ")"
#     
# group = "{" (setting-list | empty) "}"
#     
# empty =
```

上面配置中设置了3台mysql，配置了可写用户root，只读用户readuser，针对某一个库的可写用户 system。proxysql可以对不同的hostgroup分配不同用户、设置不同sql分离规则。上面hostgroup 0 可写，hostgroup 1只读

启动（为了配置直接能看到，所以用下面方式重启）

```
/etc/init.d/proxysql stop && rm -f /var/lib/proxysql/* && /etc/init.d/proxysql start
```

登录

```
mysql -uadmin -padmin -h127.0.0.1 -P6032
 
select * from mysql_servers;
select * from mysql_users;
SELECT hostgroup hg, sum_time, count_star, digest_text FROM stats_mysql_query_digest ORDER BY sum_time DESC;
select * from stats_mysql_processlist;
```

查看状态

```
proxysql-status admin admin 127.0.0.1 6032
```

测试

```
for i in {0..100};do mysql -ureaduser -p654321 -h(keepalived IP) -e "SELECT @@server_id;" ;done
```

常用命令

```
mysql -uadmin -padmin -h127.0.0.1 -P6032
 
select * from mysql_users;
select hostgroup_id,hostname,port,status,weight from mysql_servers;
select username,password,transaction_persistent,active,backend,frontend,max_connections from runtime_mysql_users;
select * from mysql_query_rules;
select * from mysql_server_connect_log;
select * from mysql_server_ping_log;
select * from mysql_server_replication_lag_log;
SELECT hostgroup hg, sum_time, count_star, digest_text FROM stats_mysql_query_digest ORDER BY sum_time DESC;
SELECT hostgroup hg, sum_time, count_star, digest_text FROM stats_mysql_query_digest where hg=1 ORDER BY sum_time DESC;
select * from stats_mysql_processlist where hostgroup=1;
SELECT 1 FROM stats_mysql_query_digest_reset LIMIT 1;
select hostgroup,username,digest_text,count_star from stats_mysql_query_digest;
select hostgroup,count_star,schemaname,username,substr(digest_text,150,-150) from stats_mysql_query_digest;
select active,hits,mysql_query_rules.rule_id, schemaname, match_digest, match_pattern, replace_pattern,destination_hostgroup hostgroup FROM mysql_query_rules NATURAL JOIN stats.stats_mysql_query_rules JOIN mysql_servers s on destination_hostgroup=hostgroup_id ORDER BY mysql_query_rules.rule_id;
```

参考文档：

<https://www.percona.com/blog/2016/09/13/proxysql-and-mha-integration/>

<https://zhubiaook.github.io/linux/2017/11/14/ProxySQL_MHA/>

<https://www.cnblogs.com/kevingrace/p/10329714.html>

<http://seanlook.com/2017/04/17/mysql-proxysql-route-rw_split/>



**mysql group replication 和proxysql结合的操作**

```
insert into mysql_servers (hostgroup_id,hostname,port,weight) values (2,'192.168.0.187',3306,1);
insert into mysql_servers (hostgroup_id,hostname,port,weight) values (2,'192.168.0.188',3306,1);
insert into mysql_servers (hostgroup_id,hostname,port,weight) values (2,'192.168.0.189',3306,1);
load mysql servers to runtime;
select * from mysql_servers;

insert into mysql_users(username,password,default_hostgroup,max_connections) values('root','123456',2,1000);
insert into mysql_users(username,password,default_hostgroup,max_connections) values('readuser','123456',2,1000);
insert into mysql_users(username,password,default_hostgroup,max_connections) values('system','123456',2,500);

load mysql servers to runtime;

insert into mysql_replication_hostgroups(writer_hostgroup,reader_hostgroup) values (2,3);

insert into mysql_group_replication_hostgroups (writer_hostgroup,backup_writer_hostgroup,reader_hostgroup, offline_hostgroup,active,max_writers,writer_is_also_reader,max_transactions_behind) values (2,4,3,1,1,1,0,100);

load mysql users to runtime;
load mysql servers to runtime;
save mysql users to disk;
save mysql servers to disk;

select hostgroup_id, hostname, port,status from runtime_mysql_servers;
select * from mysql_server_group_replication_log order by time_start_us desc limit 3;
select hostgroup,digest_text from stats_mysql_query_digest;
```

2019年07月11日 于 [linux工匠](http://www.bbotte.com/) 发表