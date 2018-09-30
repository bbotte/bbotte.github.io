#!/bin/bash
#适用于centos 7，更改hostname和password
echo "------------"
echo "Please set HostName! default is localhost "
echo "if don't want to change, click Enter"
read -p "HostName is:>>  " changehost
if [[ $changehost != "" ]];then
hostnamectl --static set-hostname $changehost
fi

echo "------------"
IP=`ip a|grep inet| sed -n '3p'|awk '{print $2}'|awk -F '/' '{print $1}'`
if [ ! -c /dev/urandom ];then yum install calc -y;fi 
PASSWD=`tr -dc '.;_A-Za-z0-9' </dev/urandom | head -c 20`
echo Passwd is changed
echo ${PASSWD}|passwd --stdin root
echo ${IP} ${PASSWD}

rm -f /root/click_me.sh
exec $SHELL
