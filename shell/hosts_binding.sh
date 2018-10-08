#!/bin/bash
# hosts 域名绑定
# yum install mail bind-utils -y
PATH=/bin:/usr/bin:/sbin:/usr/sbin
#需要绑定域名列表
iplist="te-code.bbotte.com code.bbotte.com "
file_name="/etc/hosts"
regex_ip="(2[0-4][0-9]|25[0-5]|1[0-9][0-9]|[1-9]?[0-9])(\.(2[0-4][0-9]|25[0-5]|1[0-9][0-9]|[1-9]?[0-9])){3}"
for i in $iplist;do
  IP=`dig +time=2 +tries=1 +short ${i} |egrep "$regex_ip"`
  if [ ! ${IP} ];then
      echo "IP resolution ${i} bad"|mail -s "Web Server IP resolution bad" zhangsan@qq.com
      continue
  fi
  n=\"$i\"
  existed_host_name=`awk '{for(m=1;m<=NF;m++){if($m=='${n}') print $2}}' $file_name`
  existed_host_ip=`awk '{for(m=1;m<=NF;m++){if($m=='${n}') print $1}}' $file_name`
  will_soon_host="$IP $i"
  if [ ! $existed_host_name ];then
      echo $will_soon_host >> $file_name
  else
      if [ $existed_host_name == $i ] && [ $existed_host_ip != $IP ];then
          sed -i "/$i/d" $file_name
          echo $will_soon_host >> $file_name
      fi
  fi
done
