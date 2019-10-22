# kubernetes代理内部服务之websocket服务

kubernetes对内部服务的代理一般用traefik、flannel、calico等，特殊情况特殊待遇，k8s并提供了NodePort从node节点直接把服务暴露出来，和external IPs使用自定义一个内网IP转发请求到内部服务等方式。下面以研发做了一个基于websocket协议的聊天服务为例，websocket服务需要外网能够直接访问，并且im服务和其他服务也有相互调用，线上服务用的kubernetes集群，之所以写这篇文章是尝试了很多方法解决websocket服务出来的实验，比如使用traefik、clusterIP、nginx、nginx+websockt多种方法都无济于事。因为service是4层，traefik是7层，加上nginx代理也提示

```
ERROR o.s.w.s.server.support.DefaultHandshakeHandler  -Handshake failed due to invalid Upgrade header: null
INFO  com.bbotte.config.WebSocketConfig  -进来webSocket的afterHandshake拦截器！
```

下面介绍一下k8s内部websocket服务被外部访问的方式

方式一：[kubernetes NodePort ](https://kubernetes.io/docs/concepts/services-networking/service/#nodeport)+ nginx keepalived

方式二：[kubernetes externalIPs](https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types) + nginx keepalived

nodeport方式使用的比较多，大部分接触是因为kubernetes dashboard的访问，即把内部服务通过一个端口暴露出来供外部访问。externallIPs是自定义一个内部的IP给服务使用，功能类似于ExternalName，即后端服务端口变动，服务也不用修改。2种种方式用到了nginx+keepalived是因为在traefik(ingress)外部加了个VIP，代理各个Node节点，配置如下：

```
map $http_upgrade $connection_upgrade {
        default upgrade;
        ''      close;
    }
upstream websocket {
    server 192.168.0.100:30100;
    server 192.168.0.101:30100;
}
server {
    listen       80;
    server_name  websocket.bbotte.com;
    access_log  /var/log/nginx/websocket.log  access;
   location / {
            proxy_pass http://websocket;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
   }
}
```

kubernetes deployment配置忽略，下面是服务配置，即im服务端口为9080，nodePort暴露出去是30100，通过nginx代理提供外部访问：

```
---
kind: Service
apiVersion: v1
metadata:
  name: im-service
  labels:
    k8s-app: im
spec:
  selector:
    k8s-app: im
  type: NodePort
  ports:
  - port: 9080
    targetPort: 9080
    nodePort: 30100
```

```
# kubectl get svc -o wide
NAME             TYPE        CLUSTER-IP       EXTERNAL-IP     PORT(S)          AGE       SELECTOR
im-service       NodePort    10.104.253.46    <none>          9080:30100/TCP   16d       k8s-app=im
```



kubernetes deployment中External IPs 配置如下：

```
---
kind: Service
apiVersion: v1
metadata:
  name: testim-service
  labels:
    k8s-app: testim
  annotations:
    kube-router.io/service.scheduler: sh
spec:
  externalIPs:
  - 192.168.0.150
  selector:
    k8s-app: testim
  ports:
  - port: 9080
    targetPort: 9080
    protocol: TCP
  sessionAffinity: ClientIP
```

使用了一个内网IP 192.168.0.150 固定IP给im服务，这时候访问192.168.0.150:9080即访问了im服务。再加一层nginx转发到外网，nginx配置这里忽略，参考上面

```
# kubectl get svc -o wide
NAME               TYPE        CLUSTER-IP       EXTERNAL-IP     PORT(S)          AGE       SELECTOR
testim-service         ClusterIP   10.102.64.27     192.168.0.150   9080/TCP         4h        k8s-app=testim
```

loadBalancerIP是云厂商使用的，比如GCE、AWS、阿里云，IDC搭建的k8s集群不能使用，感觉externalIPs是内部网络的loadBalancerIP，都是提供一个固定IP

2018年07月23日 于 [linux工匠](http://www.bbotte.com/) 发表