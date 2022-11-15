#!/bin/bash
# 删除多余的docker包，每个镜像名称只保留最新的一个，docker 镜像格式为  名称-时间戳-git commitid ，排序和筛选都用到了时间戳，所以镜像tag中需要包含时间戳，比如 harbor.bbotte.com/dev/system:uat-7a84b40118-20220819174427

下面 2022 需要修改

docker images|sort -rn|awk '{print $1,$2,$3}'|awk  'gsub(/[[:blank:]]*/,"",$2){print $1,$2,"    ",$NF}'|grep 2022|while read i;do if [[ $NAME == $(echo $i|awk '{print $1}') ]];then echo $i;fi;NAME=$(echo $i|awk '{print $1}');done|awk '{print $NF}'|xargs docker rmi

删除 none的镜像
docker images|sort -rn|awk '{print $1,$2,$3}'|awk  'gsub(/[[:blank:]]*/,"",$2){print $1,$2,"    ",$NF}'|grep none|awk '{print $NF}'|xargs docker rmi


# 为了避免删镜像的时候磁盘IO过高，所以加sleep
# docker images|sort -rn|awk '{print $1,$2,$3}'|awk  'gsub(/[[:blank:]]*/,"",$2){print $1,$2,"    ",$NF}'|awk '{print $2,$NF}'|awk 'x[$1]++' |awk '{print $2}'|uniq -c|awk '{print $2}'|while read i;do docker rmi $i;sleep 0.02;done

# /var/lib/docker/overlay2 文件夹占用磁盘大，可以使用docker 系统命令删除
docker system df -v

docker system prune
