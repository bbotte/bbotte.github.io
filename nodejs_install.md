### nodejs找不到？给你安装教程

###### 一键安装

如果是Debian：

```
curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo apt-get install -y build-essential
```

如果是centos系：

```
yum install gcc-c++ make
curl --silent --location https://rpm.nodesource.com/setup_6.x | bash -
yum -y install nodejs
```

###### 使用rvm安装ruby

```
yum install gcc-c++ patch readline readline-devel zlib zlib-devel
yum install libyaml-devel libffi-devel openssl-devel make
yum install bzip2 autoconf automake libtool bison iconv-devel sqlite-devel

curl -sSL https://rvm.io/mpapis.asc | gpg --import -
curl -L get.rvm.io | bash -s stable

source /etc/profile.d/rvm.sh
rvm reload

rvm requirements run
rvm install 2.2.4
rvm use 2.2.4 --default
ruby --version
```

###### jenkins上调用nodejs发生的问题

```
jenkins on windows
npm ERR! syscall: 'rmdir' 
npm ERR!   syscall: 'scandir'
```

解决方式

```
remove node_modules
npm cache verify
npm install
```

###### linux平台安装nodejs给jenkins使用

```
tar -xf node-v8.11.1-linux-x64.tar.xz -C /usr/local/
ln -s /usr/local/node-v8.11.1-linux-x64/ /usr/local/node
cat >> /etc/profile << EOF
export PATH=$PATH:/usr/local/node/bin
EOF
. /etc/profile

npm install -g cnpm --registry=https://registry.npm.taobao.org
ln -s /usr/local/node/bin/cnpm /usr/bin/cnpm
ln -s /usr/local/node/bin/node /usr/bin/node
ln -s /usr/local/node/bin/npm /usr/local/bin/npm
ln -s /usr/local/lib/node /usr/lib/node
ln -s /usr/local/bin/npm /usr/bin/npm
yum install bzip2 -y

systemctl restart jenkins
cnpm install
```

