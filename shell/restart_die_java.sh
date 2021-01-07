#!/bin/bash
# crontab add this
# */10 * * * * /opt/shell/restart_die_java.sh
MailArray=(112233445566@qq.com )

if [ $(dirname $0) != "." ];then base_dir=$(dirname $0);else base_dir=$(pwd);fi
ProjectList="market system"

for ProjectName in $ProjectList ;do
    ServicePort=$(grep -w $ProjectName $base_dir/ServicePort|awk '{print $2}')
    if [ -z $ServicePort ];then echo $ProjectName port is not define;break ;fi
    count=0
    for (( k=0; k<2; k++ ))
    do
        check_code=$( curl -XPOST -m 3 --connect-timeout 2 -sL -w "%{http_code}\\n" http://127.0.0.1:${ServicePort} -o /dev/null)
        if [ "$check_code" != "200" ]; then
            count=$(expr $count + 1)
            sleep 10
            continue
        else
            count=0
        fi
    done
    if [ "$count" != "0" ]; then
        echo `date +%Y-%m-%d:%H:%M:%S` ${ProjectName} is not respose > /tmp/servicenores
        # restart ${ProjectName}
        echo `date +%Y-%m-%d:%H:%M:%S` ${ProjectName} api not respose|mail -s "restart java shell:project error" ${MailArray[*]}
    fi
done


#cat ServicePort
#market 8000
#system 9000