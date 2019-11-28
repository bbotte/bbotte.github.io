#!/bin/bash
#docker-compose服务的发布脚本
#cat ServiceVersion
#system:dev-201807031821-103c53bd
PATH=/bin:/usr/bin:/sbin:/usr/sbin
echo -e "\033[30;33m如果新增加服务,需要修改脚本的 ProjectList \033[0m"
base_dir=$(dirname $0)
ProjectList="system task "
if [ ! -f $base_dir/ServiceVersion ];then echo ServiceVersion file is not find;exit 1;fi
for ProjectName in $ProjectList ;do
    ProjectVersion=`grep -w $ProjectName $base_dir/ServiceVersion|awk -F':' '{print $2}'`
    OldVersion=`grep -w "$ProjectName" $base_dir/docker-compose.yml|grep "image:"|awk -F':' '{print $4}'`
    if [[ ! -n $OldVersion ]];then echo $ProjectName version is null, please write casual, like 1234 ;exit 1;fi
    if [[ -n $ProjectVersion && $ProjectVersion != $OldVersion ]];then
        ChangeLine=`grep -wn "$ProjectName" $base_dir/docker-compose.yml|grep image:|awk -F':' '{print $1}'`
        sed -i "${ChangeLine}s/$OldVersion/$ProjectVersion/" $base_dir/docker-compose.yml
        echo -e "\033[30;33m$ProjectName old_version:\033[0m" $OldVersion, "\033[30;32mnow_version:\033[0m" $ProjectVersion
        docker-compose up -d ${ProjectName}-com
    fi
done

if [[ -n $1 && $1 == "allstart" ]];then for i in $ProjectList ;do docker-compose up -d ${i}-com ;done;fi
if [[ -n $1 && $1 == "allstop" ]];then for i in $ProjectList ;do docker-compose stop ${i}-com ;done;fi
if [[ -n $1 && $1 == "allrestart" ]];then for j in $ProjectList ;do docker-compose stop ${j}-com;sleep 1; docker-compose up -d ${j}-com ;done;fi
if [[ $1 == "restart" && -n $2 ]];then docker-compose stop ${2}-com;sleep 1; docker-compose up -d ${2}-com ;fi

