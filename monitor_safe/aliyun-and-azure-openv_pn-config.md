---
layout: default
---

# 阿里云和微软云openV_PN配置

阿里云aliyun和微软云azure OpenV_PN配置

**aliyun openv_pn**
服务端：

```
# cat /etc/centos-release
CentOS Linux release 7.3.1611 (Core)
# yum install openssl openssl-devel lzo openvpn easy-rsa -y
# cd /usr/share/easy-rsa/2.0/
# egrep -v "^$|^#" /usr/share/easy-rsa/2.0/vars 
export EASY_RSA="`pwd`"
export OPENSSL="openssl"
export PKCS11TOOL="pkcs11-tool"
export GREP="grep"
export KEY_CONFIG=`$EASY_RSA/whichopensslcnf $EASY_RSA`
export KEY_DIR="$EASY_RSA/keys"
echo NOTE: If you run ./clean-all, I will be doing a rm -rf on $KEY_DIR
export PKCS11_MODULE_PATH="dummy"
export PKCS11_PIN="dummy"
export KEY_SIZE=2048
export CA_EXPIRE=3650
export KEY_EXPIRE=3650
export KEY_COUNTRY="CN" #国家
export KEY_PROVINCE="SHANGHAI" #省份
export KEY_CITY="SHANGHAI" #城市
export KEY_ORG="BBOTTE" #组织
export KEY_EMAIL="bbotte@163.com"
export KEY_OU="devops"
export KEY_NAME="aliyun"
```

清除目录下的key

```
# ./clean-all
```

生成ca证书

```
# ./build-ca
```

生成服务器证书

```
# ./build-key-server server
```

生成用户证书，用户登录使用

```
# ./build-key bbotte
```

生成 Diffie Hellman

```
# ./build-dh
```

生成ta证书

```
# openvpn --genkey --secret keys/ta.key
# mkdir /var/log/openvpn
# cd /usr/share/easy-rsa/2.0/keys 
# cp ca.crt server.crt server.key dh2048.pem ta.key /etc/openvpn/keys/
# cp /usr/share/doc/openvpn-2.4.3/sample/sample-config-files/server.conf /etc/openvpn/
```

egrep -v “^$|^#” /etc/openvpn/server.conf

```
local 139.224.*.* #阿里云服务器公网ip
port 1194
proto udp
dev tun
ca keys/ca.crt
cert keys/server.crt
key keys/server.key
dh keys/dh2048.pem
server 172.16.0.0 255.255.255.0 #阿里云主机内网ip段
ifconfig-pool-persist ipp.txt
push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 223.5.5.5"
client-to-client
keepalive 10 120
tls-auth keys/ta.key 0
cipher AES-256-CBC
comp-lzo
max-clients 100
user nobody
group nobody
persist-key
persist-tun
status openvpn-status.log
log /var/log/openvpn/openvpn.log
log-append /var/log/openvpn/openvpn.log
verb 4
mute 20
explicit-exit-notify 1
```

```
push  "route 192.168.1.0 255.255.255.0"    #向客户端推送内网网段
push  "route 192.168.100.0 255.255.255.0"  #推送VPN网段
push  "dhcp-option DNS 192.168.100.154"    #推送首选DNS，可以多个
push  "dhcp-option DNS 223.5.5.5"
client-to-client                           #允许OpenVPN客户端之间通信
```

添加 iptables 规则确保服务器可以转发数据包到阿里云内外网：

```
# iptables -t nat -A POSTROUTING -s 172.16.0.0/24 -j MASQUERADE
# echo 1 > /proc/sys/net/ipv4/ip_forward
```

启动openvpn服务

```
systemctl start openvpn@server.service;systemctl status openvpn@server.service
```

客户端：
下载客户端 <http://build.openvpn.net/downloads/releases/>
openvpn-install-2.4_rc2-I601.exe

把/usr/share/easy-rsa/2.0/keys目录中，ca.crt,bbotte.crt,bbotte.csr.bbotte.key,ta.key复制到客户端的配置目录
C:\Program Files\OpenVPN\config
并编辑openVPN的配置文件：
client.ovpn

```
client
dev tun
proto udp
remote 139.224.*.* 1194
resolv-retry infinite
nobind
persist-key
persist-tun
ca ca.crt
remote-cert-tls server
tls-auth ta.key 1
cipher AES-256-CBC
verb 3
comp-lzo
 
cert bbotte.crt
key bbotte.key
```

打开ipip.net查看本机的ip地址是否变为阿里云ip
**azure微软云**openVPN配置，步骤同上

```
# egrep -v "^$|^#" /etc/openvpn/server.conf 
local 0.0.0.0
port 1194
proto udp
dev tun
ca keys/ca.crt
cert keys/server.crt
key keys/server.key # This file should be kept secret
dh keys/dh2048.pem
server 172.18.0.0 255.255.255.0 #azure主机内网ip地址段
ifconfig-pool-persist ipp.txt
push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 223.5.5.5"
client-to-client
keepalive 10 120
tls-auth keys/ta.key 0 # This file is secret
cipher AES-256-CBC
comp-lzo
max-clients 100
persist-key
persist-tun
status openvpn-status.log
log /var/log/openvpn/openvpn.log
log-append openvpn.log
verb 3
mute 20
explicit-exit-notify 1
```

配置路由和ip转发

```
# iptables -t nat -A POSTROUTING -s 172.18.0.0/24 -j MASQUERADE
# echo 1 > /proc/sys/net/ipv4/ip_forward
# systemctl restart openvpn@server.service
```

客户端配置只有外网ip和上述阿里云不一致

2017年09月29日 于 [linux工匠](https://bbotte.github.io/) 发表