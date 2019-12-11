#### tengine install

小于2.3版本tengine

```
yum install openssl-devel pcre-dev lua-devel
tar -xf tengine-2.2.3.tar.gz
cd tengine-2.2.3
wget https://ftp.pcre.org/pub/pcre/pcre-8.40.tar.gz
tar -xf pcre-8.40.tar.gz
./configure --prefix=/usr/local/nginx --with-http_gzip_static_module --with-http_stub_status_module --with-http_lua_module  --with-http_realip_module --with-http_gunzip_module --with-pcre=./pcre-8.40
make -j2
make install
```

```
cat >> /etc/profile << EOF
export PATH=\$PATH:/usr/local/nginx/sbin/
EOF
. /etc/profile
```

```
# nginx -V
Tengine version: Tengine/2.2.3 (nginx/1.8.1)
built by gcc 4.8.5 20150623 (Red Hat 4.8.5-28) (GCC) 
TLS SNI support enabled
configure arguments: --user=nginx --group=nginx --prefix=/usr/local/nginx --with-http_lua_module --with-http_stub_status_module --with-http_ssl_module --with-http_gzip_static_module --with-http_realip_module --with-http_sub_module --with-http_upstream_check_module
```

大于2.3版本tengine

tengine 2.3.0

```
yum install openssl-devel pcre-dev lua-devel readline-devel gcc-c++ gcc -y
wget https://tengine.taobao.org/download/tengine-2.3.0.tar.gz
tar -xf tengine-2.3.0.tar.gz && cd tengine-2.3.0
wget https://ftp.pcre.org/pub/pcre/pcre-8.40.tar.gz
tar -xf pcre-8.40.tar.gz
./configure --prefix=/usr/local/nginx --with-http_gzip_static_module --with-http_stub_status_module --with-http_realip_module --with-http_gunzip_module --with-pcre=./pcre-8.40  --with-http_sub_module --add-module=modules/ngx_http_upstream_check_module
make -j2
make install
```

start on power on

```
# cat nginx.service
#/usr/lib/systemd/system/nginx.service
[Unit]
Description=nginx - high performance web server
Documentation=http://nginx.org/en/docs/
After=network-online.target remote-fs.target nss-lookup.target
Wants=network-online.target

[Service]
Type=forking
PIDFile=/var/run/nginx.pid
ExecStart=/usr/local/nginx/sbin/nginx -c /usr/local/nginx/conf/nginx.conf
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID

[Install]
WantedBy=multi-user.target
```

systemctl enable nginx

systemctl start nginx