#!/bin/bash
# 删除多余的docker包，每个镜像名称只保留最新的一个
docker images|sort -rn|grep harbor.bbotte.com|grep -v k8s|awk '{print $1,$2,$3}'|awk -F'-' 'gsub(/[[:blank:]]*/,"",$2){print $1,$2,"    ",$NF}'|awk '{print $2,$NF}'|awk 'x[$1]++' |awk '{print $2}'|xargs docker rmi
