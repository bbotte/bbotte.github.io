### 阿里蜻蜓-基于P2P镜像及文件分发系统

服务端运行

#####0.3版本

```
docker run --name dragonfly-supernode --restart=always -d -p 8001:8001 -p 8002:8002 -v /opt/dragonfly/:/home/admin/supernode dragonflyoss/supernode:0.3.0 -Dsupernode.advertiseIp=192.168.0.151
```

supernode.advertiseIp为服务端ip，这个ip需要客户端能访问，这里我服务端ip为192.168.0.151

```
# docker logs --tail 2 dragonfly-supernode
2020-11-26 06:48:54.085  INFO 11 --- [           main] o.s.j.e.a.AnnotationMBeanExporter        : Registering beans for JMX exposure on startup
2020-11-26 06:48:54.142  INFO 11 --- [           main] o.s.b.w.embedded.tomcat.TomcatWebServer  : Tomcat started on port(s): 8080 (http) with context path ''
```

#####0.4版本

```
docker run -d --name supernode --restart=always -p 8001:8001 -p 8002:8002 -v /opt/dragonfly:/home/admin/supernode dragonflyoss-supernode:0.4.3 --download-port=8001
```

0.4版本不需要supernode.advertiseIp参数

```
# less /opt/dragonfly/logs/app.log
2020-11-26 07:04:22.630 ERRO sign:11 : failed to init properties: open /etc/dragonfly/supernode.yml: no such file or directory
2020-11-26 07:04:22.630 INFO sign:11 : success to init local ip of supernode, use ip: 172.17.0.2
2020-11-26 07:04:22.630 INFO sign:11 : start to run supernode
2020-11-26 07:05:26.420 INFO sign:11 : success to register peer &{IP:172.18.1.2 HostName:b29e2ac74680 Port:19581 Version:0.4.3}
```



客户端运行

```
cat <<EOD > /etc/dragonfly.conf
[node]
address=192.168.0.151
EOD
```

```
docker run -d --name dfclient --restart=always -p 65001:65001 -v /etc/dragonfly.conf:/etc/dragonfly.conf dragonflyoss-dfclient:0.4.3 --registry http://harbor.bbotte.com --node 192.168.0.151
```

需要设置docker的登录，拉取镜像使用http://127.0.0.1:65001代替原来的http://harbor.bbotte.com

```
# cat /etc/docker/daemon.json 
{
  "insecure-registries": ["http://harbor.bbotte.com"],
  "registry-mirrors": ["http://127.0.0.1:65001"]
}

systemctl restart docker
systemctl status docker

docker login http://127.0.0.1:65001 -u admin -p AbCd\@\^\&
docker pull 127.0.0.1:65001/demo/aftersales:demo-201906151620-a1478c0d
```




客户端验证
```
# docker exec dfclient grep 'downloading piece' /root/.small-dragonfly/logs/dfclient.log
2020-11-26 06:53:33.022 INFO sign:49-1606373612.547 : downloading piece:{"taskID":"36ecb778104b369c1cf988160951b4a86d439c583c9c8eb07fd7d20b91dca783","superNode":"192.168.0.151:8002","dstCid":"","range":"","result":502,"status":700,"pieceSize":0,"pieceNum":0}
```



[Dragonfly官方文档](https://d7y.io/zh-cn/index.html)