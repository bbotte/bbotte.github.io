---
layout: default
---

# 升级glibc解决GLIBC_2.14 not found

使用hadoop命令时候，总会遇到GLIBC_2.14 not found 如下提示，需要升级glibc的版本

```
WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
```

在log4j里面添加加载项的debug日志

```
# vim /usr/local/hadoop/etc/hadoop/log4j.properties
log4j.logger.org.apache.hadoop.util.NativeCodeLoader=DEBUG
# start-dfs.sh
DEBUG util.NativeCodeLoader: Trying to load the custom-built native-hadoop library...
DEBUG util.NativeCodeLoader: Failed to load native-hadoop with error: java.lang.UnsatisfiedLinkError: /usr/local/hadoop-2.6.4/lib/native/libhadoop.so.1.0.0: /lib64/libc.so.6: version `GLIBC_2.14' not found (required by /usr/local/hadoop-2.6.4/lib/native/libhadoop.so.1.0.0)
DEBUG util.NativeCodeLoader: java.library.path=/usr/local/hadoop-2.6.4/lib/native
WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
```

得到提示GLIBC_2.14木有找到，需要安装高版本的glibc以解决问题

1，查看现在系统的glibc版本

```
# strings /lib64/libc.so.6 |grep GLIBC_
GLIBC_2.2.5
GLIBC_2.2.6
GLIBC_2.3
GLIBC_2.3.2
GLIBC_2.3.3
GLIBC_2.3.4
GLIBC_2.4
GLIBC_2.5
GLIBC_2.6
GLIBC_2.7
GLIBC_2.8
GLIBC_2.9
GLIBC_2.10
GLIBC_2.11
GLIBC_2.12
GLIBC_PRIVATE
```

2，安装glibc 2.19版本

```
wget http://mirrors.ustc.edu.cn/gnu/libc/glibc-2.19.tar.xz
tar -xf glibc-2.19.tar.xz
mkdir glibc-2.19/build
cd glibc-2.19/build
../configure  --prefix=/usr --enable-profile --enable-add-ons --with-headers=/usr/include --with-binutils=/usr/bin
make -j2
make install
#安装完毕
ldconfig
# ll /lib64/libc*
-rwxr-xr-x. 1 root root  1923352 5月  10 22:11 /lib64/libc-2.12.so
-rwxr-xr-x  1 root root 10053895 8月  23 16:23 /lib64/libc-2.19.so
lrwxrwxrwx. 1 root root       18 8月   5 10:27 /lib64/libcap-ng.so.0 -> libcap-ng.so.0.0.0
-rwxr-xr-x. 1 root root    18672 6月  25 2011 /lib64/libcap-ng.so.0.0.0
lrwxrwxrwx. 1 root root       14 8月   5 10:27 /lib64/libcap.so.2 -> libcap.so.2.16
-rwxr-xr-x. 1 root root    16600 12月  8 2011 /lib64/libcap.so.2.16
-rwxr-xr-x. 1 root root   197064 5月  10 22:11 /lib64/libcidn-2.12.so
-rwxr-xr-x  1 root root   268553 8月  23 16:23 /lib64/libcidn-2.19.so
lrwxrwxrwx  1 root root       15 8月  23 16:23 /lib64/libcidn.so.1 -> libcidn-2.19.so
lrwxrwxrwx. 1 root root       17 8月   5 10:27 /lib64/libcom_err.so.2 -> libcom_err.so.2.1
-rwxr-xr-x. 1 root root    14664 7月  24 2015 /lib64/libcom_err.so.2.1
-rwxr-xr-x. 1 root root    40400 5月  10 22:11 /lib64/libcrypt-2.12.so
-rwxr-xr-x  1 root root   151060 8月  23 16:22 /lib64/libcrypt-2.19.so
lrwxrwxrwx. 1 root root       22 8月   5 10:27 /lib64/libcryptsetup.so.1 -> libcryptsetup.so.1.1.0
-rwxr-xr-x. 1 root root    94736 10月 15 2014 /lib64/libcryptsetup.so.1.1.0
lrwxrwxrwx  1 root root       16 8月  23 16:23 /lib64/libcrypt.so.1 -> libcrypt-2.19.so
lrwxrwxrwx  1 root root       12 8月  23 16:23 /lib64/libc.so.6 -> libc-2.19.so
# strings /lib64/libc.so.6 |grep GLIBC
GLIBC_2.2.5
GLIBC_2.2.6
GLIBC_2.3
GLIBC_2.3.2
GLIBC_2.3.3
GLIBC_2.3.4
GLIBC_2.4
GLIBC_2.5
GLIBC_2.6
GLIBC_2.7
GLIBC_2.8
GLIBC_2.9
GLIBC_2.10
GLIBC_2.11
GLIBC_2.12
GLIBC_2.13
GLIBC_2.14
GLIBC_2.15
GLIBC_2.16
GLIBC_2.17
GLIBC_2.18
GLIBC_PRIVATE
```

因为glibc版本问题hadoop或者adb的使用都会有遇到，记下来以供分享

2016年08月24日 于 [linux工匠](http://www.bbotte.com/) 发表