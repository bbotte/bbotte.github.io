---
layout: default
---

# 编译kubernetes二进制文件

编译kubectl、kubelet、kubeadm等二进制命令

现在kubernetes主流版本是1.8，官网下载go，版本需大于1.9，编译主机内存4G，6G剩余磁盘空间（2g内存，磁盘空间小于6g是不会成功的）

<https://github.com/kubernetes/community/blob/master/contributors/devel/development.md>

<https://kubernetes.io/docs/setup/release/building-from-source/>

<https://github.com/kubernetes/kubernetes/tree/master/build/>

```
go1.9.2.linux-amd64.tar.gz
tar -xf go1.9.2.linux-amd64.tar.gz -C /usr/local
export PATH=$PATH:/usr/local/go/bin
yum install gcc rsync -y
```

获取最新的源码

```
go get -d k8s.io/kubernetes
cd go/src/k8s.io/kubernetes
```

或者GitHub按版本标签下载指定版本的源码，解压后进入目录开始编译

![编译kubernetes二进制文件 - 第1张](../images/2017/12/%E5%BE%AE%E4%BF%A1%E6%88%AA%E5%9B%BE_20171213100523.png)

```
# KUBE_BUILD_PLATFORMS=linux/amd64 make all
......
/opt/kubernetes-1.8.2 /opt/kubernetes-1.8.2/test/e2e/generated
/opt/kubernetes-1.8.2/test/e2e/generated
+++ [1207 02:46:51] Building go targets for linux/amd64:
cmd/kube-proxy
cmd/kube-apiserver
cmd/kube-controller-manager
cmd/cloud-controller-manager
cmd/kubelet
cmd/kubeadm
cmd/hyperkube
vendor/k8s.io/kube-aggregator
vendor/k8s.io/apiextensions-apiserver
plugin/cmd/kube-scheduler
cmd/kubectl
federation/cmd/kubefed
cmd/gendocs
cmd/genkubedocs
cmd/genman
cmd/genyaml
cmd/genswaggertypedocs
cmd/linkcheck
federation/cmd/genfeddocs
vendor/github.com/onsi/ginkgo/ginkgo
test/e2e/e2e.test
cmd/kubemark
vendor/github.com/onsi/ginkgo/ginkgo
test/e2e_node/e2e_node.test
cmd/gke-certificates-controller
```

编译后查看生成目录

```
# ls _output/local/go/bin
apiextensions-apiserver   genfeddocs                   hyperkube                kubemark
cloud-controller-manager  genkubedocs                  kubeadm                  kube-proxy
conversion-gen            genman                       kube-aggregator          kube-scheduler
deepcopy-gen              genswaggertypedocs           kube-apiserver           linkcheck
defaulter-gen             genyaml                      kube-controller-manager  openapi-gen
e2e_node.test             ginkgo                       kubectl                  teststale
e2e.test                  gke-certificates-controller  kubefed
gendocs                   go-bindata                   kubelet
```

附：

1，选择某一个版本编译

```
export GOPATH=~/
go get github.com/whateveruser/whateverrepo
cd ~/src/github.com/whateveruser/whateverrepo
git tag -l
# supose tag v0.0.2 is correct version
git checkout tags/v0.0.2
go run whateverpackage/main.go
```

2，关于GOPATH和GOROOT

Edit your ~/.bash_profile to add the following line:

```
export GOPATH=$HOME/go
```

Save and exit your editor. Then, source your ~/.bash_profile.

```
source ~/.bash_profile
```

Note: Set the GOBIN path to generate a binary file when go install is run.

```
export GOBIN=$HOME/go/bin
```

GOPATH环境变量是为了列出了寻找Go代码的地方

export GOTPAHT = {源代码路径，src的上一级文件夹}

想要把go安装到哪个目录，就

```
export GOROOT=目录路径
```

2017年12月13日 于 [linux工匠](https://bbotte.github.io/) 发表