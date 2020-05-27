---
layout: default
---

# harbor私有仓库镜像的推拉弹唱

harbor仓库有私有和公开2个访问级别，公开的话，不用密码就可以访问，没有安全性，下面介绍私有仓库的认证方式
在kubernetes官网有介绍创建docker-registry secret

```
kubectl create secret docker-registry SECRET_NAME --namespace=NAME_SPACE --docker-server=DOCKER_REGISTRY_SERVER --docker-username=DOCKER_USER --docker-password=DOCKER_PASSWORD --docker-email=DOCKER_EMAIL
```

这里没有采用上面方式，下面是创建拉取私有镜像的2种方式
1,首先命令行登录harbor，查看docker登录的信息

```
docker login harbor.bbotte.com:5000 -u admin -p haha\!@%^
 
# cat /root/.docker/config.json 
{
	"auths": {
		"harbor.bbotte.com:5000": {
			"auth": "AAABBBCCCDDD"
		},
		"hub.bbotte.com": {
			"auth": "AAABBBCCCDDD"
		}
	}
}
```

可以看一下记录的密码： echo AAABBBCCCDDD |base64 -d
2,获取docker-registry经base64加密的字符串

```
# base64 -w 0 .docker/config.json 
AAABBBCCCDDDAAABBBCCCDDDAAABBBCCCDDDAAABBBCCCDDDAAABBBCCCDDD
```

3,创建secret和serviceaccount

```
# cat docker-registry-auth.yaml
apiVersion: v1
kind: Secret
metadata:
  name: harbor-auth
  namespace: default
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: AAABBBCCCDDDAAABBBCCCDDDAAABBBCCCDDDAAABBBCCCDDDAAABBBCCCDDD #这里是上面获取的加密字符串
 
 
# kubectl create -f yaml/harbor-auth.yaml 
secret "harbor-auth" created
```

4,查看生成的认证信息

```
# kubectl get secret|grep harbor
harbor-auth kubernetes.io/dockerconfigjson 1 1h
```

5,使用secret认证

```
apiVersion: v1
kind: Pod
metadata:
  name: testnginx
spec:
  containers:
  - name: testnginx
    image: harbor.bbotte.com:5000/devops/nginx:0.1
    imagePullPolicy: Always
  imagePullSecrets:
  - name: harbor-auth
```

也有说把.docker目录复制到kubelet就可以，node节点比较多，没测试
cp /root/.docker /var/lib/kubelet/

harbor结构：

<https://github.com/vmware/harbor/wiki/Architecture-Overview-of-Harbor>

2018年06月25日 于 [linux工匠](https://bbotte.github.io/) 发表