# (转载)Nginx代理解决跨域问题分析

 酒香逢  原文链接 https://www.cnblogs.com/fnz0/p/15803011.html

当你遇到跨域问题，不要立刻就选择复制去尝试。请详细看完这篇文章再处理 。我相信它能帮到你。

分析前准备：

前端网站地址：http://localhost:8080

服务端网址：http://localhost:59200 

首先保证服务端是没有处理跨域的，其次，先用postman测试服务端接口是正常的

请求接口返回200状态码

当网站8080去访问服务端接口时，就产生了跨域问题，那么如何解决？接下来我把跨域遇到的各种情况都列举出来并通过nginx代理的方式解决（后台也是一样的，只要你理解的原理）。

跨域主要涉及4个响应头：

- Access-Control-Allow-Origin 用于设置允许跨域请求源地址 （预检请求和正式请求在跨域时候都会验证）

- Access-Control-Allow-Headers 跨域允许携带的特殊头信息字段 （只在预检请求验证）

- Access-Control-Allow-Methods 跨域允许的请求方法或者说HTTP动词 （只在预检请求验证）

- Access-Control-Allow-Credentials 是否允许跨域使用cookies，如果要跨域使用cookies，可以添加上此请求响应头，值设为true（设置或者不设置，都不会影响请求发送，只会影响在跨域时候是否要携带cookies，但是如果设置，预检请求和正式请求都需要设置）。不过不建议跨域使用（项目中用到过，不过不稳定，有些浏览器带不过去），除非必要，因为有很多方案可以代替。

网上很多文章都是告诉你直接Nginx添加这几个响应头信息就能解决跨域，当然大部分情况是能解决，但是我相信还是有很多情况，明明配置上了，也同样会报跨域问题。

什么是预检请求？：当发生跨域条件时候，览器先询问服务器，当前网页所在的域名是否在服务器的许可名单之中，以及可以使用哪些HTTP动词和头信息字段。只有得到肯定答复，浏览器才会发出正式的XMLHttpRequest请求，否则就报错。如下图

[](https://img2020.cnblogs.com/blog/785963/202201/785963-20220117153920730-744089560.png)

1，发送预检请求，状态码为204，得到服务器认可后发送正式请求
2，发送正式请求，状态码为200

开始动手模拟：

Nginx代理端口：22222 ,配置如下

```
server {
        listen       22222;
        server_name  localhost;
        location  / {
            proxy_pass  http://localhost:59200;
        }
}
```

测试代理是否成功，通过Nginx代理端口2222再次访问接口，可以看到如下图通过代理后接口也是能正常访问
[](https://img2020.cnblogs.com/blog/785963/202201/785963-20220114173102937-2013447545.png)

curl http://localhost:22222/api/Login/TestGet
返回200

接下来开始用网站8080访问Nginx代理后的接口地址，报错情况如下↓↓↓

情况1： 

Access to XMLHttpRequest at 'http://localhost:22222/api/Login/TestGet' from origin 'http://localhost:8080' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
[](https://img2020.cnblogs.com/blog/785963/202201/785963-20220114173436625-731892550.png)


通过错误信息可以很清晰的定位到错误（注意看标红部分）priflight说明是个预请求，CORS 机制跨域会首先进行 preflight（一个 OPTIONS 请求）， 该请求成功后才会发送真正的请求。 这一设计旨在确保服务器对 CORS 标准知情，以保护不支持 CORS 的旧服务器

通过错误信息，我们可以得到是预检请求的请求响应头缺少了 Access-Control-Allow-Origin，错哪里，我们改哪里就好了。修改Nginx配置信息如下（红色部分为添加部分），缺什么就补什么，很简单明了

```
server {
        listen       22222;
        server_name  localhost;
        location  / {
           add_header Access-Control-Allow-Origin 'http://localhost:8080';
           proxy_pass  http://localhost:59200; 
        }
    }
```

当满怀欢喜的以为能解决后，发现还是报了同样的问题
[](https://img2020.cnblogs.com/blog/785963/202201/785963-20220114173436625-731892550.png)


不过我们的配置没什么问题,问题在Nginx,下图链接 [ngx_http_headers_module](http://nginx.org/en/docs/http/ngx_http_headers_module.html)

[](https://img2020.cnblogs.com/blog/785963/202201/785963-20220114175210362-1233993158.png)

add_header 指令用于添加返回头字段，当且仅当状态码为图中列出的那些时有效。如果想要每次响应信息都携带头字段信息，需要在最后添加always（经我测试，只有Access-Control-Allow-Origin这个头信息需要加always，其他的不加always也会携带回来），那我们加上试试

```
server {
        listen       22222;
        server_name  localhost;
        location  / {
           add_header Access-Control-Allow-Origin 'http://localhost:8080' always;
           proxy_pass  http://localhost:59200; 
        }
    }
```

修改了配置后，发现生效了，当然不是跨域就解决了，是上面这个问题已经解决了，因为报错内容已经变了

情况2：

Access to XMLHttpRequest at 'http://localhost:22222/api/Login/TestGet' from origin 'http://localhost:8080' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: It does not have HTTP ok status.

[](https://img2020.cnblogs.com/blog/785963/202201/785963-20220114175942594-1648328371.png)

通过报错信息提示可以得知，是跨域浏览器默认行为的预请求（option请求）没有收到ok状态码，此时再修改配置文件，当请求为option请求时候，给浏览器返回一个状态码（一般是204）

```
 server {
        listen       22222;
        server_name  localhost;
        location  / {
           add_header Access-Control-Allow-Origin 'http://localhost:8080' always;
           if ($request_method = 'OPTIONS') {
                return 204;
           }
           proxy_pass  http://localhost:59200; 
        }
    }
```
当配置完后，发现报错信息变了

情况3：

Access to XMLHttpRequest at 'http://localhost:22222/api/Login/TestGet' from origin 'http://localhost:8080' has been blocked by CORS policy: Request header field authorization is not allowed by Access-Control-Allow-Headers in preflight response.
[](https://img2020.cnblogs.com/blog/785963/202201/785963-20220114180636169-124050448.png)
 

意思就是预请求响应头Access-Control-Allow-Headers中缺少头信息authorization（各种情况会不一样，在发生跨域后，在自定义添加的头信息是不允许的，需要添加到请求响应头Access-Control-Allow-Headers中，以便浏览器知道此头信息的携带是服务器承认合法的，我这里携带的是authorization，其他的可能是token之类的，缺什么加什么），知道了问题所在，然后修改配置文件，添加对应缺少的部分，再试试

```
server {
        listen       22222;
        server_name  localhost;
        location  / {
           add_header Access-Control-Allow-Origin 'http://localhost:8080' always;
           if ($request_method = 'OPTIONS') {
               add_header Access-Control-Allow-Headers 'authorization'; #为什么写在if里面而不是接着Access-Control-Allow-Origin往下写？因为这里只有预检请求才会检查
               return 204; 
          } 
        proxy_pass http://localhost:59200; 
    }
}
```
此时发现报错问题又回到了情况1
[](https://img2020.cnblogs.com/blog/785963/202201/785963-20220117155355037-633157008.png)


 

经测试验证，只要if ($request_method = 'OPTIONS') 里面写了 add_header ，当为预检请求时外部配置的都会失效，为什么？ ↓↓。

官方文档是这样说的：

There could be several add_header directives. These directives are inherited from the previous level if and only if there are no add_header directives defined on the current level.

意思就是当前层级无 add_header 指令时，则继承上一层级的add_header。相反的若当前层级有了add_header，就应该无法继承上一层的add_header。

[](https://img2020.cnblogs.com/blog/785963/202201/785963-20220117170051866-1452056778.png)

 
配置修改如下：

```
server {
        listen       22222;
        server_name  localhost;
        location  / {
            add_header Access-Control-Allow-Origin 'http://localhost:8080' always;
            if ($request_method = 'OPTIONS') {
                add_header Access-Control-Allow-Origin 'http://localhost:8080';
                add_header Access-Control-Allow-Headers 'authorization';
                return 204;
            }
            proxy_pass  http://localhost:59200; 
        }
    }
```
此时改完发现跨域问题已经解决了，



不过以上虽然解决了跨域问题，但是考虑后期可能Nginx版本更新,不知道这个规则会不会被修改，考虑到这样的写法可能会携带上两个 Access-Control-Allow-Origin ，这种情况也是不允许的，下面会说到。所以配置适当修改如下：


```
server {
        listen       22222;
        server_name  localhost;
        location  / {
            if ($request_method = 'OPTIONS') {
                add_header Access-Control-Allow-Origin 'http://localhost:8080';
                add_header Access-Control-Allow-Headers 'authorization';
                return 204;
            }
            if ($request_method != 'OPTIONS') {
                add_header Access-Control-Allow-Origin 'http://localhost:8080' always;
            }
            proxy_pass  http://localhost:59200; 
        }
    }
```

还没完，继续聊 ↓↓

情况4：

比较早期的API可能只用到了POST和GET请求，而Access-Control-Allow-Methods这个请求响应头跨域默认只支持POST和GET，当出现其他请求类型时候，同样会出现跨域异常。

比如，我这里将请求的API接口请求方式从原来的GET改成PUT，在发起一次试试。在控制台上会抛出错误：

Access to XMLHttpRequest at 'http://localhost:22222/api/Login/TestGet' from origin 'http://localhost:8080' has been blocked by CORS policy: Method PUT is not allowed by Access-Control-Allow-Methods in preflight response.
[](https://img2020.cnblogs.com/blog/785963/202201/785963-20220115114849336-791620711.png)


报错内容也讲的很清楚，在这个预请求中，PUT方法是不允许在跨域中使用的，我们需要改下Access-Control-Allow-Methods的配置(缺什么加上么，这里我只加了PUT，可以自己加全一点)，让浏览器知道服务端是允许的

```
server {
    listen 22222;
    server_name localhost;
    location / {
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin 'http://localhost:8080';
            add_header Access-Control-Allow-Headers 'content-type,authorization';
            add_header Access-Control-Allow-Methods 'PUT';#为这么只加在这个if中，不再下面的if也加上？因为这里只有预检请求会校验，当然你加上也没事。
            return 204;
        }
        if ($request_method != 'OPTIONS') {
            add_header Access-Control-Allow-Origin 'http://localhost:8080' always;
        }
        proxy_pass http://localhost:59200;
    }
}

 ```

这里注意一下，改成PUT类型后，Access-Control-Allow-Headers请求响应头又会自动校验content-type这个请求头，和情况3是一样的，缺啥补啥就行了。如果不加上content-type，则会报如下错误。（想简单的话，Access-Control-Allow-Headers和Access-Control-Allow-Methods可以设置为 * ,表示全都匹配。但是Access-Control-Allow-Origin就不建议设置成 * 了，为了安全考虑，限制域名是很有必要的。）
[](https://img2020.cnblogs.com/blog/785963/202201/785963-20220115115620797-412445312.png)


都加上后，问题就解决了，这里报405是我服务端这个接口只开放了GET，没有开放PUT，而此刻我将此接口用PUT方法去请求，所以接口会返回这个状态码。

```
405 Method Not Allowed
```


情况5：

最后再说一种情况，就是后端处理了跨域，就不需要自己在处理了（这里吐槽下，某些后端工程师自己改服务端代码解决跨域，但是又不理解其中原理，网上随便找段代码黏贴，导致响应信息可能处理不完全，如method没添加全，headers没加到点上，自己用的那个可能复制过来的并不包含实际项目所用到的，没有添加options请求返回状态码等，导致Nginx再用通用的配置就会可能报以下异常）

Access to XMLHttpRequest at 'http://localhost:22222/api/Login/TestGet' from origin 'http://localhost:8080' has been blocked by CORS policy: The 'Access-Control-Allow-Origin' header contains multiple values '*, http://localhost:8080', but only one is allowed.

[](https://img2020.cnblogs.com/blog/785963/202201/785963-20220117113435504-1619332974.png)
 

意思就是此刻Access-Control-Allow-Origin请求响应头返回了多个，而只允许有一个，这种情况当然修改配置去掉Access-Control-Allow-Origin这个配置就可以了，不过遇到这种情况，建议Nginx配置和服务端自己解决跨域只选其一。（这里注意如果按我上面的写法，if $request_method = 'OPTIONS' 这个里面的Access-Control-Allow-Origin可不能删除，删除!='OPTIONS'里面的就好了，因为这里如果是预检请求直接就ruturn了，请求不会再转发到59200服务，如果也删除了，就会报和情况1一样的错误。所以为什么说要不服务端代码层面解决跨域，要不就Nginx代理解决，不要混着搞，不然不明白原理的人，网上找一段代码贴就很可能解决不了问题）

 ↓ ↓ ↓ ↓ ↓

再贴一份完整配置（*号根据自己‘喜好’填写）：

```
server {
        listen       22222;
        server_name  localhost;
        location  / {
            if ($request_method = 'OPTIONS') {
                add_header Access-Control-Allow-Origin 'http://localhost:8080';
                add_header Access-Control-Allow-Headers '*';
                add_header Access-Control-Allow-Methods '*';
                add_header Access-Control-Allow-Credentials 'true';
                return 204;
            }
            if ($request_method != 'OPTIONS') {
                add_header Access-Control-Allow-Origin 'http://localhost:8080' always;
                add_header Access-Control-Allow-Credentials 'true';
            }
            proxy_pass  http://localhost:59200; 
        }
    }
```
或者：

```
server {
        listen       22222;
        server_name  localhost;
        location  / {
            add_header Access-Control-Allow-Origin 'http://localhost:8080' always;
            add_header Access-Control-Allow-Headers '*';
            add_header Access-Control-Allow-Methods '*';
            add_header Access-Control-Allow-Credentials 'true';
            if ($request_method = 'OPTIONS') {
                return 204;
            }
            proxy_pass  http://localhost:59200; 
        }
    }

 ```

最后，这是一篇解决跨域遇到问题解决问题的过程，如果认真看完了，我相信应该都能很容易的理解，并且在实际使用中自己解决该问题，希望能帮助到大家，以上内容都是自己理解自己测试码出来的，如有理解不对的地方，望大家指正。
