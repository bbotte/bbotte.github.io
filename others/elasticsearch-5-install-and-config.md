# elasticsearch5安装和配置

1. es的安装
2. es的配置
3. head插件的安装
4. head插件的配置
5. head插件的运行
6. 服务启动及关闭
7. ELK日志流程

elasticsearch5安装和配置
elasticsearch版本：5.4.1
云主机系统版本：CentOS 7.3

### **es的安装**

```
sudo模式下的安装
sudo yum install vim lrzsz git gcc-c++ make -y
sudo rpm -ivh http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-9.noarch.rpm
sudo rpm -ivh elasticsearch-5.4.1.rpm
sudo rpm -ivh jdk-8u66-linux-x64.rpm
sudo mkdir -p /data/elasticsearch/{db,logs}
sudo chown sudo_user.sudo_user -R /etc/elasticsearch/
sudo chmod 644 /etc/elasticsearch/*
sudo mkdir -p /usr/share/elasticsearch/config/scripts
chmod 755 /etc/elasticsearch/
chmod 777 -R /data/elasticsearch
sudo ln -s /etc/elasticsearch/ /usr/share/elasticsearch/config
```

```
rpm -ivh jdk-8u66-linux-x64.rpm 
fdisk -l
root模式下安装
yum install xfsprogs -y
fdisk /dev/sdc
mkfs.xfs -f /dev/sdc1 
echo "/dev/sdc1 /data xfs defaults 0 0" >> /etc/fstab
mkdir /data
mount -a
df -h
 
mkdir -p /data/elasticsearch/{db,logs}
chown -R elasticsearch.elasticsearch /data/es
```

### **es的配置**

```
egrep -v "^$|^#" /etc/elasticsearch/elasticsearch.yml
 
cluster.name: bbotte
node.name: bbotte-one
path.data: /data/elasticsearch/db
path.logs: /data/elasticsearch/logs
network.host: 10.2.2.9
http.port: 9200
discovery.zen.ping.unicast.hosts: ["10.2.2.10", "10.2.2.11"]  #三台es，ip是9,10,11
http.cors.enabled: true
http.cors.allow-origin: "*"                    #这里是为了es-head插件
 
sudo /etc/init.d/elasticsearch restart
```

此版本的es，只能通过curl的put方法更改分片数量，而不是配置文件中设置

```
curl -XPUT 'http://localhost:9200/_all/_settings?preserve_existing=true' -d '{
  "index.number_of_replicas" : "1",
  "index.number_of_shards" : "5"
}'
```

elasticsearch的head插件

### **head插件的安装**

```
# cat /etc/yum.repos.d/nodesource-el.repo 
[nodesource]
name=Node.js Packages for Enterprise Linux 6 - $basearch
baseurl=https://rpm.nodesource.com/pub_6.x/el/6/$basearch
failovermethod=priority
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/NODESOURCE-GPG-SIGNING-KEY-EL
 
[nodesource-source]
name=Node.js for Enterprise Linux 6 - $basearch - Source
baseurl=https://rpm.nodesource.com/pub_6.x/el/6/SRPMS
failovermethod=priority
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/NODESOURCE-GPG-SIGNING-KEY-EL
gpgcheck=1
 
sudo yum -y install nodejs
 
git clone git://github.com/mobz/elasticsearch-head.git
cd elasticsearch-head/
sudo npm install
```

### **head插件的配置**

Gruntfile.js中对grunt的设置：

```
vim Gruntfile.js
 
connect: {
    server: {
        options: {
            hostname: '10.2.2.9',
            port: 9100,
            base: '.',
            keepalive: true
            }
        }
    }
```

app.js中对es的配置：

```
vim _site/app.js
 
this.base_uri = this.config.base_uri || this.prefs.get("app-base_uri") || "http://127.0.0.1:9200";
```

### **head插件的运行**

```
./node_modules/grunt/bin/grunt server
或者
npm run start
```

### 服务启动及关闭

```
es:
sudo /etc/init.d/elasticsearch restart
 
logstash:
sudo systemctl status/restart logstash
 
kibana:
sudo /etc/init.d/kibana restart
 
es-head:
cd /data/elasticsearch-head/;nohup npm run start >/dev/null 2>&1 &
```

logstash和kibana都用rpm包安装

### ELK日志流程

```
------------------      ----------      -----------------      -----------------
app-server生成log  |    |          |    |                 |    |                 |
                  |----|kafka     |----|logstash indexer |----|elasticsearch db |
logstash shipper  |    |          |    |                 |    |                 |
------------------     -----------      -----------------     ------------------
```



2017年09月20日 于 [linux工匠](http://www.bbotte.com/) 发表