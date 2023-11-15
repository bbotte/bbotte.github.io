---
layout: default
---

# nginx-rewrite重定向跳转实例

工作中常用到nginx的rewrite，网上许多文章也写了一些，不过实用性的话，还是往下看吧。

nginx重定向-跳转实例:

1，将www.a.com/connect 跳转到connect.a.com

```
rewrite ^/connect$ http://connect.a.com permanent;
```

2，将connect.a.com 301跳转到www.a.com/connect/

```
if ($host = "connect.a.com"){
rewrite ^/(.*)$ http://www.a.com/connect/$1 permanent;
}
```

3，a.com 跳转到www.a.com

```
if ($host != 'www.a.com' ) { 
rewrite ^/(.*)$ http://www.a.com/$1 permanent; 
}
```

4，www.a.com/category/123.html 跳转为 category/?cd=123

```
rewrite "/category/(.*).html$" /category/?cd=$1 last;
```

5，www.a.com/admin/ 下跳转为www.a.com/admin/index.php?s=

```
if (!-e $request_filename){
rewrite ^/admin/(.*)$ /admin/index.php?s=/$1 last;
}
```

6，在后面添加/index.php?s=

```
if (!-e $request_filename){
    rewrite ^/(.*)$ /index.php?s=/$1 last;
}
```

7，www.a.com/xinwen/123.html  等xinwen下面数字+html的链接跳转为404

```
rewrite ^/xinwen/([0-9]+)\.html$ /404.html last;
```

8，http://www.a.com/news/radaier.html 301跳转 http://www.a.com/strategy/

```
rewrite ^/news/radaier.html http://www.a.com/strategy/ permanent;
```

9，重定向 链接为404页面

```
rewrite http://www.a.com/123/456.php /404.html last;
```

10, 禁止htaccess

```
location ~//.ht {
         deny all;
     }
```

11, 可以禁止/data/下多级目录下.log.txt等请求;

```
location ~ ^/data {
     deny all;
     }
```

12, 禁止单个文件

```
location ~ /www/log/123.log {
      deny all;
     }
```

13, 将http://test.com/news/activies/2014-08-26/123.html 跳转为 http://a.com/news/activies/123.html

```
rewrite ^/news/activies/2014\-([0-9]+)\-([0-9]+)/(.*)$ http://a.com/news/activies/$3 permanent;
```

14，nginx多条件重定向rewrite

如果需要打开带有play的链接就跳转到play，不过/admin/play这个不能跳转

```
if ($request_filename ~ (.*)/play){ set $payvar '1';}
if ($request_filename ~ (.*)/admin){ set $payvar '0';}
if ($payvar ~ '1'){
       rewrite ^/ http://play.a.com/ break;
        }
```

15，http://www.a.com/?gid=6 跳转为http://www.a.com/123.html

```
 if ($request_uri ~ "/\?gid\=6"){return  http://www.a.com/123.html;}
```

16,公司有主站（电脑端）和微站（手机访问），同一个域名，需要跳转到相应目录：

```
server_name www.a.com;
index index.html index.htm;
 
root /www/a/;
location / {
    if ( $http_user_agent ~ "(WAP)|(Mobile)|(iPhone)|(Android)|(WindowsCE)|(Opera)"){
          root /www/a/wap;
          }
    }
```

17,访问http://www.abc.com?url=https://test.github.io 301到 https://test.github.io

```
if ($request_uri ~ "/\?url\=(.*)"){ return 301 $1 ;}
或者
if ($query_string ~ "url=(\w+)") { return 301 $arg_url;}
```

下面来个实战，好好看看nginx rewrite的强大：

需求如下

```
http://m.a.com/wap/改为http://wap.a.com/
http://m.a.com/xb2/wap/改为http://wap.a.com/xb2/
http://m.a.com/xb2/wap/news/ 改为http://wap.a.com/xb2/zh/xw/
http://m.a.com/xb2/wap/radier/改为http://wap.a.com/xb2/yxgl/
http://m.a.com/wap/game_list/改为：http://wap.a.com/game/
http://m.a.com/wap/game_list/games/?id=10改为http://wap.a.com/game/list/?id=10
```

```
set $arg 0;
if ($request_filename ~ m.a.com/xb2/wap){ set $arg "${arg}1" ;}
if ($request_filename ~ m.a.com/xb2/wap/news){ set $arg "${arg}11"; }
if ($request_filename ~ m.a.com/xb2/wap/radier){ set $arg "${arg}111"; }
    if ($arg = '01'){rewrite ^/ http://wap.a.com/xb2/ permanent;}
    if ($arg = '0111'){  rewrite ^/ http://wap.a.com/xb2/zh/xw permanent;}
    if ($arg = '01111'){  rewrite ^/ http://wap.a.com/xb2/yxgl permanent;}
 
set $arg 0;
if ($request_filename ~ m.a.com/wap/game_list){ set $arg "${arg}1" ;}
if ($request_filename ~ m.a.com/wap/game_list/games/(.*)$){ set $arg "${arg}11"; }
    if ($arg = '01'){  rewrite ^/ http://wap.a.com/game/ permanent;}
    if ($arg = '0111'){  rewrite ^/ http://wap.a.com/game/list/$1 permanent;}
 
if ($request_filename ~ "m.a.com/wap/"){rewrite ^/(.*)$  http://wap.a.com/ permanent;}
```

17, 现在我们用阿里云、七牛的免费ssl证书，对nginx的http跳转https rewrite如下

```
server {
        listen  80;
        server_name test.com www.test.com;
        return 301 https://test.com$request_uri;
}
```

变量的说明： [var_request_uri](http://nginx.org/en/docs/http/ngx_http_core_module.html#var_request_uri)，比如：

`$request_uri：`full original request URI (with arguments)

`$request_method：`request method, usually “`GET`” or “`POST`”

`$request_filename：`file path for the current request, based on the [root](http://nginx.org/en/docs/http/ngx_http_core_module.html#root) or [alias](http://nginx.org/en/docs/http/ngx_http_core_module.html#alias) directives, and the request URI

18.多个条件的跳转

```
       location / {
            if ($test ~* '^abcd$|^xyz$') {
                 proxy_pass http://test_com;
            }
        }
```

curl -H "test:abcd" http://localhost

正则表达式匹配，其中：

~ 为区分大小写匹配

~* 为不区分大小写匹配

!~和!~*分别为区分大小写不匹配及不区分大小写不匹配

文件及目录匹配，其中：

-f和!-f用来判断是否存在文件

-d和!-d用来判断是否存在目录

-e和!-e用来判断是否存在文件或目录

-x和!-x用来判断文件是否可执行

flag标记有：

last 相当于Apache里的[L]标记，表示完成rewrite

break 终止匹配, 不再匹配后面的规则

redirect 返回302临时重定向 地址栏会显示跳转后的地址

permanent 返回301永久重定向 地址栏会显示跳转后的地址

下面和nginx重定向没有关系，只是资源路径有多个

```
location ~.*\(htm|html|gif|jpg|jpeg|png|bmp|swf|js|css)$ {
        root /usr/local/nginx/www/img;
        if (! -f $request_filename)
        {
         root /var/www/html/img;
        }
        if (! -f $request_filename)
        {
        root /apps/images;
        } 
  }
```

有些时候rewrite的功能可以用proxy_pass实现，比如

```
rewrite ^/a/(.*)$ http://b.com/abcd/a/$1 permanent;
```

```
location  /a/ {
        proxy_pass http://b.com/abcd/a/;
    }

```

nginx中配置proxy_pass代理转发，如果在proxy_pass后面的url加/，表示绝对根路径

如果没有/，表示相对路径，把匹配的路径部分也给代理

下面四种情况都用 http://127.0.0.1/proxy/test.html 进行访问

第一种：

```
location /proxy/ {
proxy_pass http://127.0.0.1/;
}
```

代理到URL：http://127.0.0.1/test.html

第二种 相对于第一种，最后少一个 / 

```
location /proxy/ {
proxy_pass http://127.0.0.1;
}
```

代理到URL：http://127.0.0.1/proxy/test.html

第三种：

```
location /proxy/ {
proxy_pass http://127.0.0.1/aaa/;
}
```

代理到URL：http://127.0.0.1/aaa/test.html

第四种 相对于第三种，最后少一个 / 

```
location /proxy/ {
proxy_pass http://127.0.0.1/aaa;
}
```

代理到URL：http://127.0.0.1/aaatest.html



2016年03月01日 于 [linux工匠](https://test.github.io/) 发表

