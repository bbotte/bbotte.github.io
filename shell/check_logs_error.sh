#!/bin/bash
PATH=/bin:/usr/bin:/sbin:/usr/sbin
#取每小时的日志时间戳跟错误日志中时间对比,日志中时间格式为17/Oct/2017:11:49:14
# 42.159.1.1 - - [05/Feb/2018:09:36:33 +0800] "POST /member-service/task/users/pull HTTP/1.1" 504 123 "-" "-" "-"
MYMAIL=(zhangsan@qq.com lisi@qq.com)
errorlognum=`awk '$9=="500" || $9=="502" || $9=="503" || $9=="504" {print}' /var/log/nginx/api.access.log|egrep -v "XYZ|okhttp" |wc -l`
errorloghead=`awk '$9=="500" || $9=="502" || $9=="503" || $9=="504" {print}' /var/log/nginx/api.access.log|awk '{printf "%s %s %s\n",$11,$6,$7}'|sed 's/"//g'|awk -F'?' '{print $1}'|sort -rn |uniq -c|sort -rn|head`
errorlog=`awk '$9=="500" || $9=="502" || $9=="503" || $9=="504" {print}' /var/log/nginx/top-api.access.log|egrep -v "XYZ|okhttp" |tail -n 1`
hourtime=`echo $errorlog|awk '{print $4}'|awk -F':' '{print $1":"$2":"$3}'|awk -F'[' '{print $2}'|sed 's/.$/0/'|sed 's#/#\ #g'|sed 's/:/\ /'`
# 这里取的时间不是精确的十分钟之前
logtimestamp=`date +%s -d"$hourtime"`
tenminutesago=`date -d'10 minutes ago' '+%Y-%m-%d %H:%M'|sed 's/.$/0/'`
nowtimestamp=`date +%s -d"$tenminutesago"`
echo $logtimestamp
echo $nowtimestamp

if [ $logtimestamp -eq $nowtimestamp ];then
    echo -e "router-top-node1 \n top-api.sao.so \n 10分钟内有50X错误日志 \n 今天50X日志总计$errorlognum 条 \n /var/log/nginx/access.log \n $errorloghead"|mail -s "router-top-node1 top-api has 50X logs" ${MYMAIL[*]}
fi


# write crontab
# */10 * * * * sh /root/top-apierror.sh
