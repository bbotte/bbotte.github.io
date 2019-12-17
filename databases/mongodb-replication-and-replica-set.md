---
layout: default
---

# mongodb的单机主从和复制集

- mongodb单机
- mongodb的主从
- mongodb的复制集
- mongodb备份和恢复
- mongdb数据库连接
- 具体配置步骤
- mongo shell

### **mongodb单机**

```
cat /etc/centos-release
CentOS Linux release 7.3.1611 (Core)
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
tar -xf mongodb-linux-x86_64-rhel70-3.4.7.tgz -C /usr/local/
ln -s /usr/local/mongodb-linux-x86_64-rhel70-3.4.7/ /usr/local/mongodb
mkdir -p /data/mongodb/{db,log}
vim /etc/profile
export PATH=/usr/local/mongodb/bin:$PATH
. /etc/profile
 
vim /etc/mongod.conf
port=27017
master=true
oplogSize=4096
dbpath=/data/mongodb/db
logpath=/data/mongodb/log/db.log
pidfilepath = /data/mongodb/log/mongo.pid
#bind_ip = * #这里是*，如果只是绑定ip，填入ip即可，比如bind_ip = 127.0.0.1,192.168.1.1
journal = true
quiet = true
nohttpinterface = true
logappend=true
fork=true
#auth=true #第一次启动不要加认证
```

服务的启动和停止

```
service start
mongod -f /etc/mongod.conf
login
mongo
 
service stop
mongo 127.0.0.1:27017/admin --eval "db.shutdownServer()"
或者 
ps aux|grep [m]ongod.conf|awk '{print $2}'|xargs kill -2
```

如果mongod非正常关闭，需要修复

```
mongod --dbpath /data/mongodb/db/ --logpath /data/mongodb/log/db.log --repair
```

mongo不加密码当然可以使用，不过最好还是加一层防护：

**不启用auth认证登录mongo**，添加管理员用户，用户名随意

```
use admin
db.createUser({ 'user' : 'admin', 'pwd' : 'bbotte.com', 'roles':[ {role:'root',db:'admin'} ] })
```

关闭mongodb

更改配置文件，**开启auth=true密码认证**

```
use admin
db.auth('admin','bbotte.com')
db.system.users.find().pretty()
#添加用户
use testdb
db.createUser({ 'user':'testmongo', 'pwd':'books.bbotte.com', 'roles':[ { role:'dbOwner', db:'testdb' } ] })
```

测试：使用新建的用户testmongo登录mongo测试

```
use testdb
db.auth('testmongo','books.bbotte.com')
db.toptest.insert({testdb:'this is test'})
show collections
db.testdb.find()
```

添加密码后启动和关闭mongod：

```
关闭mongodb
use admin
db.auth('admin','bbotte.com')
show dbs
db.shutdownServer()
 
启动mongod
mongod -f /etc/mongod.conf
```

### **mongodb的主从**

根据上面mongodb的单机来做，步骤一样，配置稍变
主库添加配置：
master = true
从库添加配置：
slave = true
source = 192.168.1.1:27017

从库执行rs.slaveOk()
\> rs.slaveOk()
\> show dbs
主库插入数据，在从库验证

### **mongodb的复制集**

<https://docs.mongodb.com/v3.0/core/replication-introduction/>
双机互信，时间同步
根据上面mongodb的单机来做，步骤有变
生成authkey，权限600，所有主机保持一致

```
openssl rand -base64 741 > /data/mongodb/log/mongodb-keyfile
```

mongodb主执行单机模式的“不启用auth认证登录mongo”，建立全局用户，然后按照下面配置

主配置：

```
# cat /etc/mongod.conf 
port=27017
#master=true
oplogSize=4096
dbpath=/data/mongodb/db
logpath=/data/mongodb/log/db.log
pidfilepath = /data/mongodb/log/mongo.pid
#bind_ip = *
journal = true
quiet = true
nohttpinterface = true
logappend=true
fork=true
#auth=true
replSet = bbotte
keyFile = /data/mongodb/log/mongodb-keyfile
```

从配置

```
# cat /etc/mongod.conf 
port=27017
#master=true
#slave = true
#source = 192.168.1.1:27017
oplogSize=4096
dbpath=/data/mongodb/db
logpath=/data/mongodb/log/db.log
pidfilepath = /data/mongodb/log/mongo.pid
#bind_ip = *
journal = true
quiet = true
nohttpinterface = true
logappend=true
fork=true
#auth=true
replSet = bbotte
keyFile = /data/mongodb/log/mongodb-keyfile
```

主mongo操作，初始化复制集：

```
# mongo
bbotte:PRIMARY> cfg={_id:'bbotte',members:[ 
{_id:0,host:'192.168.1.1:27017'}, 
{_id:1,host:'192.168.1.2:27017'}] 
}
bbotte:PRIMARY> rs.initiate(cfg)
{
"ok" : 0,
"errmsg" : "not authorized on admin to execute command { replSetInitiate: { _id: \"bbotte\", members: [ { _id: 0.0, host: \"192.168.1.1:27017\" }, { _id: 1.0, host: \"192.168.1.2:27017\" } ] } }",
"code" : 13,
"codeName" : "Unauthorized"
}
 
bbotte:PRIMARY> use admin
switched to db admin
bbotte:PRIMARY> db.auth('admin','bbotte.com')
1
bbotte:PRIMARY> rs.status()
```

rs.status()查看mongodb复制集的状态

现在mongodb复制集已经完成，随后创建一个用户，附加权限给一个数据库，再测试

创建用户：
执行单机模式的创建用户那一段“开启auth=true密码认证”
在从库查看验证：

```
# mongo
MongoDB shell version v3.4.7
connecting to: mongodb://127.0.0.1:27017
MongoDB server version: 3.4.7
bbotte:SECONDARY> use admin
switched to db admin
bbotte:SECONDARY> db.auth('admin','bbotte.com')
1
bbotte:SECONDARY> rs.status()
bbotte:SECONDARY> rs.slaveOk()
bbotte:SECONDARY> show dbs
```

如果继续添加一个节点
<https://docs.mongodb.com/v3.0/tutorial/deploy-replica-set/>

```
rs.add('192.168.1.3:27017')
```

\#rs.addArb是添加仲裁者https://docs.mongodb.com/v3.0/reference/method/rs.addArb/#rs.addArb

arbiter节点配置如下：

```
# cat /etc/mongod.conf 
port=27017
#master=true
oplogSize=4096
dbpath=/data/mongodb/db
logpath=/data/mongodb/log/db.log
pidfilepath = /data/mongodb/log/mongo.pid
#bind_ip = *
#arbiter node,set journal = flase
journal = false
quiet = true
nohttpinterface = true
logappend=true
fork=true
#auth=true
replSet = bbotte
keyFile = /data/mongodb/log/mongodb-keyfile
```

上面配置，需要先执行单机模式的“不启用auth认证登录mongo”，建立全局用户

```
rs.addArb('192.168.1.3:27017')
rs.status()
```

//重新配置即可

```
rs.reconfig(rs.conf())
#通过定义配置更改可以这样保存，比如 conf={}，然后rs.reconfig(rs.conf())
#如果是  rs.add 或 rs.addArb 系统会直接保存配置
```

### mongodb备份和恢复

```
mongodump --host 127.0.0.1 --port 27017 --username user --password 'pass' --db dbname --archive=/opt/dbname_`date +%F`
mongorestore --host 127.0.0.1 --port 27017 --username user --password 'pass' --archive /opt/dbname_`date +%F`
```

```
mongodump --host 192.168.1.1 --port 27017 --username admin --password 'pass' --db def --ssl -o /opt/mongodb_bakup
mongorestore  --host 192.168.1.1 --port 27017 --username admin --password 'pass' --ssl  --sslAllowInvalidCertificates /opt/mongodb_bakup
```

### mongdb数据库连接

```
mongo --host 192.168.1.1:27017 -u admin -p 'XXXX' --authenticationDatabase admin
mongostat -h 192.168.1.1:27017 -u admin -p 'XXXX' --authenticationDatabase=admin
```

更多文档参考<https://docs.mongodb.com/manual/introduction/>

<https://docs.mongodb.com/manual/tutorial/deploy-replica-set/>

<https://help.aliyun.com/document_detail/52344.html?spm=5176.doc51059.6.621.qQnIG2>

### 具体配置步骤

```
yum安装mongodb及复制集的配置
centos 7.3
同步时间，双机互信
# cat /etc/yum.repos.d/mongo.repo 
[mongodb-org-3.4]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/3.4/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-3.4.asc
 
yum install -y mongodb-org
yum erase $(rpm -qa | grep mongodb-org)  #卸载
 
三台主机用同样的认证文件keyfile
openssl rand -base64 741 > /data/mongodb/log/mongodb-keyfile
chmod 600 /var/log/mongodb/mongodb-keyfile
chown mongod.mongod /var/log/mongodb/mongodb-keyfile
# egrep -v "^$|^#" /etc/mongod.conf 
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
storage:
  dbPath: /var/lib/mongo
  journal:
    enabled: true
processManagement:
  fork: true  # fork and run in background
  pidFilePath: /var/run/mongodb/mongod.pid  # location of pidfile
net:
  port: 27018
  bindIp: 172.18.2.22
 
# systemctl start mongod
# systemctl status mongod
# mongo 172.18.2.22:27018/admin
use admin
db.createUser({ 'user' : 'bbotte', 'pwd' : '123456', 'roles':[ {role:'root',db:'admin'} ] })
exit
# systemctl stop mongod
 
# egrep -v "^$|^#" /etc/mongod.conf 
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
storage:
  dbPath: /var/lib/mongo
  journal:
    enabled: true
processManagement:
  fork: true  # fork and run in background
  pidFilePath: /var/run/mongodb/mongod.pid  # location of pidfile
net:
  port: 27018
  bindIp: 172.18.2.22  # Listen to local interface only, comment to listen on all interfaces.
security:
  keyFile: /var/log/mongodb/mongodb-keyfile
replication:
  replSetName: bbotte
 
三台主机都如上配置，不过bindIP是各自的ipaddress，另外第三台主机是arbiter节点
journal:
  enabled: false
 
# systemctl start mongod
# mongo 172.18.2.22:27018/admin
> use admin
switched to db admin
> db.auth('bbotte','123456')
1
> rs.initiate()
{
	"info2" : "no configuration specified. Using a default configuration for the set",
	"me" : "172.18.2.22:27018",
	"ok" : 1
}
bbotte:SECONDARY> 
bbotte:PRIMARY> rs.add("172.18.1.17:27018")
{ "ok" : 1 }
bbotte:PRIMARY> rs.status()
此时已添加一个节点，下面再添加arbiter节点
bbotte:PRIMARY> rs.addArb('172.18.1.18:27018')
{ "ok" : 1 }
bbotte:PRIMARY> rs.status()
bbotte:PRIMARY> db.serverStatus()
bbotte:PRIMARY> db.serverStatus().connections.available
bbotte:PRIMARY> show dbs
```

更改权重

```
bbotte:PRIMARY> cfg=rs.conf()
bbotte:PRIMARY> cfg.members[0].priority = 3
bbotte:PRIMARY> cfg.members[1].priority = 2
bbotte:PRIMARY> rs.reconfig(cfg)
{ "ok" : 1 }
bbotte:PRIMARY> rs.config()
 
#删除节点
rs.remove("192.168.1.1:27017")
```

从库读：

```
bbotte:SECONDARY> rs.slaveOk()
bbotte:SECONDARY> show dbs
```

### mongo shell

```
mongo --host 192.168.1.1:27017 -u admin -p 'password' --authenticationDatabase admin --eval "rs.status()" |grep -B 3 PRIMARY
			"name" : "192.168.11.1:27017",
			"health" : 1,
			"state" : 1,
			"stateStr" : "PRIMARY",
```

mongo用 –eval 参数传递命令

2017年09月05日 于 [linux工匠](http://www.bbotte.com/) 发表