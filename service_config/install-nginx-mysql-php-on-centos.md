# 生产环境Centos编译安装Nginx-MySQL-php

LNMP安装是对系统服务熟悉的一个入门，想起来当时接触linux的时候，花了2个月时间一步一步编译安装成功，把lnmp作为一个基础，收获较大，现在php很少来用了，此文致予刚步入linux系统的新手，希望在编译安装使用过程中了解linux的应用和乐趣。

Centos6.6 64位最小化安装,版本如下：

MySQL-5.6.19 php-5.5.14 nginx-1.6.0
cmake2.8.7   libiconv-1.14   libmcrypt-2.5.8   mhash-0.9.9   zlib-1.2.5   libpng-1.6.2   freetype-2.4.12   jpegsrc.v9   gettext-0.18.1.1   mcrypt-2.6.8   memcache-2.2.7   ImageMagick-6.8.8-9   imagick-3.1.2   pcre-8.35
php模块：
pthreads.so，redis.so，map.so，memcache.so，imagick.so，opcache.so，mongo.so
服务重新加载

```
service nginx reload
service php-fpm reload
service mysqld restart
```

配置文件路径：

```
nginx： /usr/local/nginx/conf/nginx.conf
php： /usr/local/php/etc/php-fpm.conf /usr/local/php/etc/php.ini
mysql： /etc/my.cnf
```

整个安装包  链接: http://pan.baidu.com/s/1kUpziTL 密码: 3yq3

```
#!/bin/bash
#CentOS6.6最小化安装
#mysql passwd 123456
#root运行此脚本
 
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
cur_dir=$(pwd)
MYSQLDATADIR=/var/mysql/data
MYSQLLOGDIR=/var/log/mysql
 
function InstallSystem()
{
cat  >> /etc/security/limits.conf << EOF
* soft nproc 65535
* hard nproc 65535
* soft nofile 65535
* hard nofile 65535
EOF
echo "ulimit -SHn 65535" >> /etc/profile
echo "ulimit -SHn 65535" >> /etc/rc.local
sed -i 's/1024/10240/' /etc/security/limits.d/90-nproc.conf
yum install vim vim-enhanced gcc gcc-c++ bash glibc wget lrzsz bc mutt unzip ntpdate sysstat dstat \
wget man mail mlocate mtr lsof iotop iptraf -y
updatedb
/sbin/ldconfig
echo "syntax on" >> /root/.vimrc
echo "set nohlsearch" >> /root/.vimrc
sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
setenforce 0
mv /etc/sysconfig/iptables /etc/sysconfig/iptables.def
cp iptables /etc/sysconfig/
service iptables restart
#echo "0 * * * * /usr/sbin/ntpdate ntp1.aliyun.com >/dev/null 2>&1 " >> /var/spool/cron/root
#rm -f /etc/localtime
#ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
ntpdate ntp1.aliyun.com;hwclock -w
cat >>  /etc/sysctl.conf <<EOF
fs.file-max = 65535
net.ipv4.tcp_max_syn_backlog = 65536
net.core.netdev_max_backlog =  32768
net.core.somaxconn = 32768
net.core.wmem_default = 8388608
net.core.rmem_default = 8388608
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_timestamps = 0
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 2
net.ipv4.tcp_tw_recycle = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_mem = 94500000 915000000 927000000
net.ipv4.tcp_max_orphans = 3276800
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 120
net.ipv4.ip_local_port_range = 1024  65535
EOF
 
#modprobe bridge
#echo "modprobe bridge" >> /etc/rc.local
/sbin/sysctl -p
 
echo "####yum install"
yum install -y gcc gcc-c++ patch make flex bison file libtool libtool-libs autoconf sqlite-devel \
libjpeg-devel libpng libpng-devel gd gd-devel freetype-devel libxml2 libxml2-devel zlib zlib-devel glib2 \
glib2-devel bzip2 bzip2-devel libevent libevent-devel ncurses ncurses-devel curl curl-devel e2fsprogs \
e2fsprogs-devel krb5-devel libidn libidn-devel gettext-devel gmp-devel unzip libcap apr* automake openssl \
openssl-devel perl compat* mpfr cpp glibc glibc-devel libgomp libstdc++-devel ppl cloog-ppl keyutils \
keyutils-libs-devel libcom_err-devel libsepol-devel krb5-devel libXpm* php-common php-gd pcre-devel openldap
rpm -ivh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
echo "####ifstat"
tar -xzf ifstat-1.1.tar.gz 
cd ifstat-1.1
./configure
make
make install
cd ..
echo "####iftop"
yum install ncurses ncurses-devel libpcap libpcap-devel -y
tar -xzf iftop-0.17.tar.gz 
cd iftop-0.17
./configure
make
make install
cd ..
echo "####htop"
tar -xzf htop-1.0.tar.gz 
cd htop-1.0
./configure
make
make install
cd ..
 
echo "export PATH=$PATH:/usr/local/bin" >> /etc/profile.d/stat.sh
. /etc/profile.d/stat.sh
}
 
function InstallMySQL5.5()
{
#安装mysql
echo "####cmake"
yum install -y gcc gcc-c++ ncurses ncurses-devel
tar -zxf cmake-2.8.7.tar.gz
cd cmake-2.8.7
./configure
make -j4 && make install
cd ..
echo "####install mysql"
/usr/sbin/groupadd mysql
/usr/sbin/useradd -g mysql mysql
mkdir -p $MYSQLDATADIR
mkdir -p $MYSQLLOGDIR
chown -R mysql.mysql $MYSQLDATADIR
chown -R mysql.mysql $MYSQLLOGDIR
tar zxf mysql-5.5.43.tar.gz
cd mysql-5.5.43
cmake -DCMAKE_BUILD_TYPE:STRING=Release -DMYSQL_USER=mysql-DCMAKE_INSTALL_PREFIX=/usr/local/mysql \
-DMYSQL_DATADIR=$MYSQLDATADIR -DSYSCONFDIR=/etc -DWITH_MYISAM_STORAGE_ENGINE=1 \
-DWITH_INNOBASE_STORAGE_ENGINE=1 -DWITH_MEMORY_STORAGE_ENGINE=1 -DWITH_ARCHIVE_STORAGE_ENGINE=1 \
-DWITH_BLACKHOLE_STORAGE_ENGINE=1 -DWITH_FEDERATED_STORAGE_ENGINE=1 -DWITH_PARTITION_STORAGE_ENGINE=1 \
-DWITH_READLINE=1 -DMYSQL_UNIX_ADDR=/var/lib/mysql/mysql.sock -DMYSQL_TCP_PORT=3306 \
-DENABLED_LOCAL_INFILE=1 -DWITH_PARTITION_STORAGE_ENGINE=1 -DEXTRA_CHARSETS=all -DWITH_SSL=yes 
-DDEFAULT_CHARSET=utf8 -DDEFAULT_COLLATION=utf8_general_ci
make -j4
make install
echo "####config mysql"
cp ./support-files/mysql.server /etc/init.d/mysqld
chmod 755 /etc/init.d/mysqld
cd ..
mv /etc/my.cnf /etc/my.cnf.bak
sed -i -e "/#insert mysql datadir/a\datadir = ${MYSQLDATADIR}\ninnodb_data_home_dir \
= ${MYSQLDATADIR}\ninnodb_log_group_home_dir = ${MYSQLLOGDIR}\nlog-error \
= ${MYSQLLOGDIR}/mysql-error.log\npid-file = ${MYSQLLOGDIR}/mysql.pid\nlog-bin \
= ${MYSQLLOGDIR}/mysql-bin\nslow_query_log_file = ${MYSQLLOGDIR}/mysql_slow.log\n"  my.cnf
cp my.cnf /etc/
/usr/local/mysql/scripts/mysql_install_db --user=mysql  --datadir=$MYSQLDATADIR --basedir=/usr/local/mysql --log-output=file
service mysqld start
yum install mysql -y
 
cat > /tmp/mysql_sec_script.sql<<EOF
use mysql;
update user set password=password('123456') where user='root';
delete from user where not (user='root') ;
delete from user where user='root' and password=''; 
drop database test;
DROP USER ''@'%';
flush privileges;
EOF
/usr/local/mysql/bin/mysqladmin -u root password 123456
mysql -uroot -p123456 -e "source /tmp/mysql_sec_script.sql"
rm -f /tmp/mysql_sec_script.sql
/usr/local/mysql/bin/mysql_secure_installation  <<EOF
123456
n
y
y
y
y
EOF
/etc/init.d/mysqld restart
ps aux|grep mysql|grep -v grep
sleep 1
}
 
function InstallMySQL5.6()
{
#mysql 5.6
yum install openssl openssl-devel ncurses ncurses-devel gcc gcc-c++ -y
tar -zxf cmake-2.8.7.tar.gz
cd cmake-2.8.7
./configure
make -j4 && make install
cd ..
tar -xzf mysql-5.6.17.tar.gz 
cd mysql-5.6.17
mkdir /work/mysql/data -p
mkdir /work/mysql/log -p
/usr/sbin/groupadd mysql
/usr/sbin/useradd -g mysql mysql
chown -R mysql.mysql /work/mysql
cmake -DCMAKE_BUILD_TYPE:STRING=Release -DCMAKE_INSTALL_PREFIX=/usr/local/mysql \
-DMYSQL_DATADIR=/work/mysql/data -DSYSCONFDIR=/etc -DWITH_MYISAM_STORAGE_ENGINE=1 \
-DWITH_INNOBASE_STORAGE_ENGINE=1 -DWITH_ARCHIVE_STORAGE_ENGINE=1 -DWITH_BLACKHOLE_STORAGE_ENGINE=1 \
-DWITH_FEDERATED_STORAGE_ENGINE=1 -DWITH_PARTITION_STORAGE_ENGINE=1 \
-DMYSQL_UNIX_ADDR=/var/lib/mysql/mysql.sock -DMYSQL_TCP_PORT=3306 -DENABLED_LOCAL_INFILE=1 \
-DWITH_PARTITION_STORAGE_ENGINE=1 -DEXTRA_CHARSETS=all -DWITH_SSL=yes -DDEFAULT_CHARSET=utf8 \
-DDEFAULT_COLLATION=utf8_general_ci
make -j4
make install
cp /etc/my.cnf{,.def}
cp ./support-files/mysql.server /etc/init.d/mysqld
chmod 755 /etc/init.d/mysqld
chkconfig --add mysqld
chkconfig mysqld on
cp my_5.6.cnf /etc/my.cnf
/usr/local/mysql/scripts/mysql_install_db --user=mysql  --datadir=/work/mysql/data/ \
--basedir=/usr/local/mysql --log-output=file --explicit_defaults_for_timestamp
yum install mysql -y
service mysqld start
cat > /tmp/mysql_sec_script.sql<<EOF
use mysql;
update user set password=password('123456') where user='root';
delete from user where not (user='root') ;
delete from user where user='root' and password=''; 
drop database test;
DROP USER ''@'%';
flush privileges;
EOF
/usr/local/mysql/bin/mysqladmin -u root password 123456
mysql -uroot -p123456 -e "source /tmp/mysql_sec_script.sql"
rm -f /tmp/mysql_sec_script.sql
/usr/local/mysql/bin/mysql_secure_installation  <<EOF
123456
n
y
y
y
y
EOF
service mysqld restart
}
 
function InstallNginx()
{
#安装nginx
echo "####pcre"
tar  -zxf pcre-8.35.tar.gz
cd pcre-8.35
./configure --prefix=/usr/local/pcre
make&&make  install
cd ../
echo "####install nginx"
groupadd www
useradd -g www www -s /sbin/nologin
tar -xzf nginx-1.6.3.tar.gz
cd  nginx-1.6.3
./configure --user=www --group=www --prefix=/usr/local/nginx --with-http_stub_status_module \
--with-http_ssl_module --with-http_gzip_static_module --with-pcre=$cur_dir/pcre-8.35 \
--with-http_realip_module --with-http_image_filter_module
make -j4
make install
cd ..
echo "####config nginx"
cp init.d.nginx /etc/init.d/nginx
chmod +x /etc/init.d/nginx
mkdir -p /var/log/nginx/
chown -R www:www /var/log/nginx
mkdir /usr/local/nginx/conf/server/
mv /usr/local/nginx/conf/nginx.conf /usr/local/nginx/conf/nginx.conf.bak
cp nginx.conf /usr/local/nginx/conf/
cp test.conf /usr/local/nginx/conf/server/
mkdir -p /var/www/test.com
cat>/var/www/test.com/index.php<< EOF
<?php
phpinfo();
?>
EOF
mv /usr/local/php/etc/php-fpm.conf /usr/local/php/etc/php-fpm.conf.bak
mkdir /var/log/php
cp php-fpm.conf /usr/local/php/etc/
echo "export PATH=$PATH:/usr/local/nginx/sbin" >> /etc/profile.d/nginx.sh
. /etc/profile.d/nginx.sh
 
echo "####redis"
tar -xzf redis-2.8.19.tar.gz
cd redis-2.8.19
make
make install
./utils/install_server.sh
service redis_6379 restart                   
redis-cli ping
}
 
function InstallPhp()
{
#安装php
echo "####libiconv"
tar zxf libiconv-1.14.tar.gz
cd libiconv-1.14
./configure --prefix=/usr/local/libs
make
make install
cd ../
echo "####libmcrypt"
tar zxf libmcrypt-2.5.8.tar.gz
cd libmcrypt-2.5.8/
./configure --prefix=/usr/local/libs
make
make install
/sbin/ldconfig
cd libltdl/
./configure --enable-ltdl-install --prefix=/usr/local/libs
make
make install
cd ../../
echo "####mhash"
tar xzf mhash-0.9.9.tar.gz
cd mhash-0.9.9
./configure --prefix=/usr/local/libs
make
make install
cd ../
echo "####zlib"
tar -zxf zlib-1.2.5.tar.gz
cd zlib-1.2.5
./configure --prefix=/usr/local/libs
make
make install
cd ../
echo "####libpng"
tar -zxf libpng-1.6.2.tar.gz
cd libpng-1.6.2
./configure --prefix=/usr/local/libs
make
make install
cd ../
echo "####freetype"
tar -zxf freetype-2.4.12.tar.gz
cd freetype-2.4.12
./configure --prefix=/usr/local/libs
make
make install
cd ../
echo "####jpegsrc"
tar -zxf jpegsrc.v9.tar.gz
cd jpeg-9
./configure  --prefix=/usr/local/libs --enable-shared --enable-static 
make
make install
cd ../
echo "####gettext"
tar -zxf gettext-0.18.1.1.tar.gz
cd gettext-0.18.1.1
./configure --prefix=/usr/local/libs
make
make install
cd ../
echo "####mcrypt"
cat > /etc/ld.so.conf.d/local.conf <<EOF
/usr/local/libs/lib
/usr/local/lib
EOF
ldconfig -v
tar zxf mcrypt-2.6.8.tar.gz
cd mcrypt-2.6.8/
export LDFLAGS="-L/usr/local/libs/lib -L/usr/lib"export CFLAGS="-I/usr/local/libs/include -I/usr/include"
export LD_LIBRARY_PATH=/usr/local/libs/: LD_LIBRARY_PATH
./configure --prefix=/usr/local/libs --with-libmcrypt-prefix=/usr/local/libs
make
make install
cd ../
echo "####install php"
cp -frp /usr/lib64/libldap* /usr/lib/
ln -s /usr/local/mysql/lib/libmysqlclient.so.18 /usr/lib64/
tar -xzf php-5.5.25.tar.gz
cd php-5.5.25
./configure --prefix=/usr/local/php --with-fpm-user=www --with-fpm-group=www \
--with-config-file-path=/usr/local/php/etc --with-openssl --with-curl --with-mysql=/usr/local/mysql \
--with-pdo-mysql=/usr/local/mysql  --with-mysqli=mysqlnd  --enable-mbstring=all --with-gd \
--with-freetype-dir=/usr/local/libs --with-jpeg-dir=/usr/local/libs --with-png-dir=/usr/local/libs \
--with-zlib-dir=/usr/local/libs --enable-mbstring --enable-sockets --with-iconv-dir=/usr/local/libs \
--enable-libxml --enable-soap --with-mcrypt=/usr/local/libs --enable-xml --enable-bcmath --enable-shmop \
--enable-sysvsem --enable-inline-optimization --enable-mbregex --enable-fpm --enable-gd-native-ttf \
--with-mhash --enable-pcntl --with-ldap --with-ldap-sasl --with-xmlrpc --enable-zip --enable-phar \
--without-pear --enable-ftp --with-mysqli=/usr/local/mysql/bin/mysql_config --enable-maintainer-zts \
--disable-rpath  --with-gettext --enable-opcache
make ZEND_EXTRA_LIBS='-liconv' -j4
make install
#php5.3的安装
#tar -xzf php-5.3.28.tar.gz 
#cd php-5.3.28
#./configure --prefix=/usr/local/php --with-fpm-user=www --with-fpm-group=www \
--with-config-file-path=/usr/local/php/etc --with-openssl --with-curl --with-mysql=/usr/local/mysql \
--with-pdo-mysql=/usr/local/mysql  --with-mysqli=mysqlnd  --enable-mbstring=all --with-gd \
--with-freetype-dir=/usr/local/libs --with-jpeg-dir=/usr/local/libs --with-png-dir=/usr/local/libs \
--with-zlib-dir=/usr/local/libs --enable-mbstring --enable-sockets --with-iconv-dir=/usr/local/libs \
--enable-libxml --enable-soap --with-mcrypt=/usr/local/libs --enable-xml --enable-bcmath --enable-shmop \
--enable-sysvsem --enable-inline-optimization --enable-mbregex --enable-fpm --enable-gd-native-ttf \
--with-mhash --enable-pcntl --with-ldap --with-ldap-sasl --with-xmlrpc --enable-zip --enable-phar \
--without-pear --enable-ftp  --disable-rpath  --with-gettext  --enable-magic-quotes 
#本机不安装mysql配置如下
#./configure --prefix=/usr/local/php --with-fpm-user=www --with-fpm-group=www \
--with-config-file-path=/usr/local/php/etc --with-openssl --with-curl --with-mysql=mysqlnd \
--with-mysqli=mysqlnd  --enable-mbstring=all --with-gd --with-freetype-dir=/usr/local/libs \
--with-jpeg-dir=/usr/local/libs --with-png-dir=/usr/local/libs --with-zlib-dir=/usr/local/libs \
--enable-mbstring --enable-sockets --with-iconv-dir=/usr/local/libs --enable-libxml --enable-soap \
--with-mcrypt=/usr/local/libs --enable-xml --enable-bcmath --enable-shmop --enable-sysvsem \
--enable-inline-optimization --enable-mbregex --enable-fpm --enable-gd-native-ttf --with-mhash \
--enable-pcntl --with-ldap --with-ldap-sasl --with-xmlrpc --enable-zip --enable-phar --without-pear \
--enable-ftp  --disable-rpath  --with-gettext  --enable-magic-quotes 
#make ZEND_EXTRA_LIBS='-liconv' -j4
#make install
echo "####config php"
ln -s /usr/local/php/bin/php /usr/bin/php
ln -s /usr/local/php/bin/phpize /usr/bin/phpize
ln -s /usr/local/php/sbin/php-fpm /usr/bin/php-fpm
cp php.ini-development /usr/local/php/etc/php.ini
cp /usr/local/php/etc/php-fpm.conf.default /usr/local/php/etc/php-fpm.conf
cp sapi/fpm/init.d.php-fpm /etc/init.d/php-fpm
chmod +x /etc/init.d/php-fpm
cd ../
sed -i 's/;date\.timezone \=/date\.timezone \= Asia\/Shanghai/g' /usr/local/php/etc/php.ini
sed -i 's/expose_php = On/expose_php = Off/g' /usr/local/php/etc/php.ini
sed -i 's/display\_errors \= On/display\_errors \= Off/g' /usr/local/php/etc/php.ini
sed -i  's/\;cgi\.fix\_pathinfo\=1/cgi\.fix\_pathinfo\=0/g' /usr/local/php/etc/php.ini
sed -i 's/display\_startup\_errors \= On/display\_startup\_errors \= Off/g' /usr/local/php/etc/php.ini
sed -i 's/disable_functions =.*/disable_functions =passthru,exec,system,chroot,scandir,chgrp,chown,\
shell_exec,proc_get_status,ini_alter,ini_alter,ini_restore,dl,openlog,syslog,readlink,symlink,popepassthru,\
escapeshellcmd,dll,popen,disk_free_space,checkdnsrr,checkdnsrr,getservbyname,getservbyport,disk_total_space,\
posix_ctermid,posix_get_last_error,posix_getcwd,posix_getegid,posix_geteuid,posix_getgid,posix_getgrgid,\
posix_getgrnam,posix_getgroups,posix_getlogin,posix_getpgid,posix_getpgrp,posix_getpid,posix_getppid,\
posix_getpwnam,posix_getpwuid,posix_getrlimit,posix_getsid,posix_getuid,posix_isatty,posix_kill,\
posix_mkfifo,posix_setegid,posix_seteuid,posix_setgid,posix_setpgid,posix_setsid,posix_setuid,\
posix_strerror,posix_times,posix_ttyname,posix_uname/g' /usr/local/php/etc/php.ini
sed -i 's/short_open_tag = Off/short_open_tag = On/g' /usr/local/php/etc/php.ini
sed -i "s#error_reporting = E_ALL#error_reporting = E_ALL \& \~E_NOTICE \& \~E_STRICT#g" /usr/local/php/etc/php.ini
sed -i "s#;error_log = syslog#error_log = /var/log/nginx/php-error#g" /usr/local/php/etc/php.ini
 
# http://pecl.php.net/package/pthreads
echo "#### pthreads"
unzip pthreads-master.zip
cd pthreads-master
/usr/local/php/bin/phpize
./configure --with-php-config=/usr/local/php/bin/php-config
make
make install
cd ..
echo "#### memcache"
tar -xzf memcache-2.2.7.tgz 
cd memcache-2.2.7
/usr/local/php/bin/phpize
./configure --with-php-config=/usr/local/php/bin/php-config
make
make install
cd ..
echo "####ImageMagick"
tar zxf ImageMagick-6.8.8-9.tar.gz
cd ImageMagick-6.8.8-9/
./configure --prefix=/usr/local/imagemagick
make -j4 && make install
cd ..
echo "####imagick"
tar -xzf imagick-3.1.2.tgz 
cd imagick-3.1.2
/usr/local/php/bin/phpize
./configure --with-php-config=/usr/local/php/bin/php-config --with-imagick=/usr/local/imagemagick
make -j4
make install
cd ..
echo "####imap"
yum install libc-client.x86_64 libc-client-devel.x86_64 -y
cp /usr/lib64/libc-client.so* /usr/lib
cd php-5.5.25/ext/imap/
phpize
./configure --with-php-config=/usr/local/php/bin/php-config --with-imap --with-imap-ssl --with-kerberos
make
make install
cd ../../../
echo "####phpredis"
unzip phpredis-master.zip
cd phpredis-master
/usr/local/php/bin/phpize
./configure --with-php-config=/usr/local/php/bin/php-config
make
make install
cd ..
echo "####mongo"
tar -xzf mongo-1.5.4.tgz 
cd mongo-1.5.4
/usr/local/php/bin/phpize 
./configure --with-php-config=/usr/local/php/bin/php-config --prefix=/usr/local/mongo
make
make install
cd ..
#echo "####ZendGuardLoader"
#tar -xzf zend-loader-php5.5-linux-x86_64.tar.gz 
#cp zend-loader-php5.5-linux-x86_64/ZendGuardLoader.so /usr/local/php/lib/php/extensions/no-debug-zts-20121212
#cat >>/usr/local/php/etc/php.ini<<EOF
#[Zend Guard]
#zend_extension = /usr/local/php/lib/php/extensions/no-debug-zts-20121212/ZendGuardLoader.so
#zend_loader.enable = 1
#zend_loader.disable_licensing = 0
#zend_loader.obfuscation_level_support = 3
#zend_loader.license_path=
#EOF
cat >>/usr/local/php/etc/php.ini<<EOF
 
extension_dir = /usr/local/php/lib/php/extensions/no-debug-zts-20121212
extension = "redis.so"
extension = "imap.so"
extension = "memcache.so"
extension = "imagick.so"
extension = "mongo.so"
extension = "pthreads.so"
[opcache]
zend_extension = /usr/local/php/lib/php/extensions/no-debug-zts-20121212/opcache.so
opcache.enable = 1
opcache.memory_consumption = 128
opcache.interned_strings_buffer = 8
opcache.max_accelerated_files = 4000
opcache.revalidate_freq = 60
opcache.fast_shutdown = 1
opcache.enable_cli = 1
EOF
}
 
function Installssh()
{
echo "####openssl"
yum install zlib zlib-devel krb5-devel.x86_64 -y
tar -xzf openssl-1.0.1g.tar.gz
cd openssl-1.0.1g
./config --prefix=/usr/local/ssl shared zlib-dynamic enable-camellia -DOPENSSL_NO_HEARTBEATS
make -j4
make install
openssl version
mv /usr/bin/openssl /usr/bin/openssl.old
mv /usr/include/openssl /usr/include/opensslold
ln -s /usr/local/ssl/bin/openssl /usr/bin/openssl
ln -s /usr/local/ssl/include/openssl/ /usr/include/openssl
echo "/usr/local/ssl/lib/" >>/etc/ld.so.conf
ldconfig -v|grep ssl
openssl version
cd ..
echo "####openssh"
yum install pam* -y
tar -xzf openssh-6.6p1.tar.gz
cd openssh-6.6p1
./configure --prefix=/usr --sysconfdir=/etc/ssh --with-pam --with-zlib --with-ssl-dir=/usr/local/ssl \
--with-md5-passwords --mandir=/usr/share/man --with-kerberos5=/usr/lib64/libkrb5.so --mandir=/usr/share/man
make
make install
ssh -V
cd ..
sed -i "s/\#Port 22/Port 30000/g" /etc/ssh/sshd_config
sed -i "s/\#PermitRootLogin yes/\#PermitRootLogin no/g" /etc/ssh/sshd_config
sed -i "s/\#UseDNS yes/\#UseDNS no/g" /etc/ssh/sshd_config
service sshd restart
}
 
function CheckService()
{
echo "####service"
service nginx restart
service php-fpm restart
service mysqld restart
chkconfig --add nginx
chkconfig --add php-fpm
chkconfig --add mysqld
chkconfig nginx on
chkconfig php-fpm on
chkconfig mysqld on
 
cat >/etc/resolv.conf <<EOF
search localdomain
nameserver 223.5.5.5
EOF
}
 
 
InstallSystem 2>&1 |tee -a /tmp/lnmp-install.log
InstallMySQL5.5  2>&1 |tee -a /tmp/lnmp-install.log
InstallPhp    2>&1 |tee -a /tmp/lnmp-install.log
InstallNginx  2>&1 |tee -a /tmp/lnmp-install.log
#Installssh    2>&1 |tee -a /tmp/lnmp-install.log
#CheckService  2>&1 |tee -a /tmp/lnmp-install.log
```

请根据自己实际情况更改

2016年02月28日 于 [linux工匠](http://www.bbotte.com/) 发表





































