---
layout: default
---

# harbor是http的前提下使用kubernetes

k8s 使用新版本1.28，harbor使用的http，没有使用证书。

```
# kubectl version
Client Version: v1.28.4

# ctr --version
ctr containerd.io 1.6.20
```
先把配置做备份

```
mv /etc/containerd/config.toml /etc/containerd/config.toml.bak
containerd config default>/etc/containerd/config.toml
systemctl restart containerd
systemctl status containerd.service
```

确定重启没问题后修改配置文件
使用官网的pause镜像，拉不下来，所以改国内,需要修改的配置在149行，
在 [plugins."io.containerd.grpc.v1.cri".registry.configs] 下面添加，
在 [plugins."io.containerd.grpc.v1.cri".registry.mirrors] 下面添加，配置如下

```
vim /etc/containerd/config.toml 
...
    sandbox_image = "registry.aliyuncs.com/google_containers/pause:3.6"
...
147     [plugins."io.containerd.grpc.v1.cri".registry.auths]
148
149     [plugins."io.containerd.grpc.v1.cri".registry.configs]
        [plugins."io.containerd.grpc.v1.cri".registry.configs."harbor.test.cn:20000"]
        [plugins."io.containerd.grpc.v1.cri".registry.configs."harbor.test.cn:20000".tls]
          ca_file = ""
          cert_file = ""
          insecure_skip_verify = true
          key_file = ""

      [plugins."io.containerd.grpc.v1.cri".registry.headers]

      [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
        [plugins."io.containerd.grpc.v1.cri".registry.mirrors."harbor.test.cn:20000"]
          endpoint = ["http://harbor.test.cn:20000"]
...
```

修改containerd配置后重启，检查状态是否正常

```
systemctl restart containerd
systemctl status containerd
```

docker已经不用了，使用的containerd 相比于docker , 多了namespace概念, 每个image和container 都会在各自的namespace下可见, 目前k8s会使用k8s.io 作为命名空间

ctr和docker对镜像的管理命令对比：

```
操作                     ctr                         docker
查看镜像              ctr images ls                 docker images
镜像导入/导出      ctr images import/exporter    docker load/save
镜像拉取/推送      ctr images pull/push              docker pull/push
镜像tag                ctr images tag                docker tag
```


完整步骤如下：

```
containerd config default>/etc/containerd/config.toml
systemctl restart containerd
sed -i 's#registry.k8s.io/pause:3.6#registry.aliyuncs.com/google_containers/pause:3.6#g' /etc/containerd/config.toml 
sed -i '/registry.configs/a\
    [plugins."io.containerd.grpc.v1.cri".registry.configs."harbor.bbotte.com:9000"]\
    [plugins."io.containerd.grpc.v1.cri".registry.configs."harbor.bbotte.com:9000".tls]\
        ca_file = ""\
        cert_file = ""\
        insecure_skip_verify = true\
        key_file = ""'  /etc/containerd/config.toml
sed -i '/registry.mirrors/a\
[plugins."io.containerd.grpc.v1.cri".registry.mirrors."harbor.bbotte.com:9000"]\
          endpoint = ["http://harbor.bbotte.com:9000"]' /etc/containerd/config.toml
systemctl restart containerd
systemctl status containerda
systemctl status containerd
```


参考[kubernetes-with-containerd-http-server](https://stackoverflow.com/questions/65724285/kubernetes-with-containerd-http-server-gave-http-response-to-https-client)

2023年12月12日 于 [linux工匠](https://bbotte.github.io/) 发表
