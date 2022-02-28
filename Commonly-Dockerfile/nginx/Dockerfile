FROM centos:centos7

LABEL maintainer="NGINX Docker Maintainers <docker-maint@nginx.com>"

ENV NGINX_VERSION 1.20.2

# 增加了upload-module模块，https://github.com/fdintino/nginx-upload-module
#ADD upload-module-2.3.0.tar.gz /home
RUN yum install -y epel-release && \
    yum install -y vim net-tools curl gcc make pcre pcre-devel zlib zlib-devel openssl openssl-devel libxslt-devel gd-devel geoip-devel shadow-utils
RUN useradd nginx
RUN CONFIG="\
		--prefix=/etc/nginx \
		--sbin-path=/usr/sbin/nginx \
		--modules-path=/usr/lib/nginx/modules \
		--conf-path=/etc/nginx/nginx.conf \
		--error-log-path=/var/log/nginx/error.log \
		--http-log-path=/var/log/nginx/access.log \
		--pid-path=/var/run/nginx.pid \
		--lock-path=/var/run/nginx.lock \
		--http-client-body-temp-path=/var/cache/nginx/client_temp \
		--http-proxy-temp-path=/var/cache/nginx/proxy_temp \
		--http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp \
		--http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp \
		--http-scgi-temp-path=/var/cache/nginx/scgi_temp \
		--user=nginx \
		--group=nginx \
		--with-http_ssl_module \
		--with-http_realip_module \
		--with-http_addition_module \
		--with-http_sub_module \
		--with-http_dav_module \
		--with-http_flv_module \
		--with-http_mp4_module \
		--with-http_gunzip_module \
		--with-http_gzip_static_module \
		--with-http_random_index_module \
		--with-http_secure_link_module \
		--with-http_stub_status_module \
		--with-http_auth_request_module \
		--with-http_xslt_module=dynamic \
		--with-http_image_filter_module=dynamic \
		--with-http_geoip_module=dynamic \
		--with-threads \
		--with-stream \
		--with-stream_ssl_module \
		--with-stream_ssl_preread_module \
		--with-stream_realip_module \
		--with-stream_geoip_module=dynamic \
		--with-http_slice_module \
		--with-mail \
		--with-mail_ssl_module \
		--with-compat \
		--with-file-aio \
		--with-http_v2_module \
#                --add-module=/home/nginx-upload-module-2.3.0 \
	" \
	&& curl -fSL https://nginx.org/download/nginx-$NGINX_VERSION.tar.gz -o nginx.tar.gz \
        && tar -xf nginx.tar.gz && rm -f nginx.tar.gz && cd nginx-$NGINX_VERSION \
	&& ./configure $CONFIG \
	&& make -j2 \
	&& make install \
	# forward request and error logs to docker log collector
	&& ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log \
        && cd ../ && rm -rf nginx-$NGINX_VERSION
RUN mkdir -p /data/logs/nginx && mkdir -p /etc/nginx/conf.d/ && mkdir -p /var/cache/nginx/{client_temp,proxy_temp,fastcgi_temp,uwsgi_temp,scgi_temp}  && chown nginx.nginx -R /var/cache/nginx
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
WORKDIR /etc/nginx/conf.d
STOPSIGNAL SIGTERM
ENV TZ=Asia/Shanghai

CMD ["nginx", "-g", "daemon off;"]
