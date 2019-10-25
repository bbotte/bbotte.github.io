# azure微软云之Azure CLI更新网络安全组

### **安装 Azure CLI**

如果是在centos主机中安装azure cli
升级npm，如果不升级的话，执行命令会提示错误

```
curl -sL https://rpm.nodesource.com/setup_6.x | bash - 
npm install -g azure-cli
```

### **登录azure**

```
azure login -e AzureChinaCloud -u your_mail@bbotte.com
```

根据提示输入密码

用户信息配置目录: ~/.azure/

tips：所有命令后面加 -h 获取帮助

### **azure的管理**

azure命令行模式分为asm(Azure服务管理)和arm(Azure资源管理)两种模式，两种模式的命令各不相同，两种模式之间可以相互切换

切换到arm模式

```
azure config mode arm
```

切换到asm模式

```
azure config mode asm
```

比如在arm模式下：

查看所有的订阅号列表

```
azure account list
```

查看所有的资源列表

```
azure resource list
```

切换到bbotte订阅号

```
azure account set bbotte
```

查看Top订阅号的资源组列表

```
azure group list
```

查看Top订阅号的vm列表

```
azure vm list
```

查看test-service资源组下 网络安全组nsg 一条安全规则default-allow-ssh的信息

```
azure network nsg rule show -g test-service -a nsg -n ssh22
```

新建一条规则

```
azure network nsg rule create -g group-service -a kafka -p '*' -o '*' -u '*' -c Allow -n work_connect-01 -f 42.1.1.1 -y 1330
 
-g 资源组
-a 网络安全组名称
-p 协议
-o 源端口范围
-u 目的端口范围
-c 允许或者拒绝
-n 添加规则名称
-f 源地址范围
-y 优先级
```

### 举例

添加网络安全组脚本可以这样写：

```
#!/bin/bash
PATH=/bin:/usr/bin:/sbin:/usr/sbin
adirname() { odir=`pwd`; cd `dirname $1`; pwd; cd "${odir}"; }
MYDIR=`adirname "$0"`
cat $MYDIR/accessip|egrep -v '^#|^$'|while read accessip;do
name=`echo $accessip|awk '{print $1}'`
ipallow=`echo $accessip|awk '{print $2}'`
priority=`echo $accessip|awk '{print $3}'`
azure network nsg rule create -g group-service -a kafka -p '*' -o '*' -u '*' -c Allow -n $name -f $ipallow -y $priority
echo $name $ipallow is add
done
 
# cat accessip 
kafka-master01    42.1.1.1   1170
```

如果登录到期，那么需要重新登录一次

2018年03月01日 于 [linux工匠](http://www.bbotte.com/) 发表