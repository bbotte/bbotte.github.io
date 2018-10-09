#!/bin/bash
#此脚本是发布java程序用，jar包位置和名称为：
# /opt/jar/system-bdbad607-master-20180807181514.jar
PATH=/bin:/usr/bin:/sbin:/usr/sbin
# ./startJavaService.sh start/stop/status/restart ServiceName 
# ./startJavaService.sh allstart/allstop/allstatus/allrestart
#如果自定义内存大小，在相同路径创建，如 systemEnv.sh
# cat systemEnv.sh
# JAVA_OPTS="-server -Xmx3g -Xms3g -Xmn256m"

ServiceName=$2
WORKSPACE="/opt/jar"
ServiceList="system task "

base_dir=$(dirname $0)

ServiceFileName() {
    JavaServiceName=
    JavaServiceName=`find ${WORKSPACE} -name "${ServiceName}*"`
}

javaopts() {
    if [ -f "$base_dir/${ServiceName}Env.sh" ]; then
      . "$base_dir/${ServiceName}Env.sh"
    else
      export JAVA_OPTS="-server -Xmx2G -Xms2G -Duser.timezone=GMT+08 "
    fi
}

checkpid() { 
    psid=0
    javaps=
    javaps=`ps aux|grep -w "jar\/${ServiceName}"|grep java |egrep -v "grep|start"|awk '{print $2}'`
    if [ -n "$javaps" ]; then
       psid=`echo $javaps`
    else
       psid=0
    fi
}

start() {
   checkpid
   if [ $psid -ne 0 ]; then
      echo -e "warn: \033[30;33m$ServiceName\033[0m already \033[42;37mstarted\033[0m (pid=$psid)"
      echo "================================"
   else
      echo -ne "Starting \033[30;33m$ServiceName\033[0m ..."
      javaopts
      ServiceFileName
      if [ -n "$JavaServiceName" ];then
          nohup java $JAVA_OPTS -jar $JavaServiceName > /dev/null 2>&1 &
          sleep 5
          checkpid
          if [ $psid -ne 0 ]; then
             echo -e "\033[42;37m[OK]\033[0m (pid=$psid)"
          else
             echo -e "\033[30;31m [Failed]\033[0m"
          fi
      else
	  echo "jar package is not found"
      fi
   fi
}

stop() {
   checkpid
   if [ $psid -ne 0 ]; then
      echo -ne "Stopping \033[30;33m$ServiceName\033[0m ...(pid=$psid) "
      kill -9 $psid
      if [ $? -eq 0 ]; then
         echo -e "\033[42;37m[OK]\033[0m"
      else
         echo -e "\033[30;31m[Failed]\033[0m"
      fi
   else
      echo -e "warn: \033[30;33m$ServiceName\033[0m is not running"
      echo "================================"
   fi
}

status() {
   checkpid
   if [ $psid -ne 0 ];  then
      echo -e "\033[30;33m$ServiceName\033[0m is \033[42;37mrunning\033[0m (pid=$psid)"
   else
      echo -e "\033[30;33m$ServiceName\033[0m is \033[30;31mnot running\033[0m"
   fi
}

allstart() {
 for ServiceName in $ServiceList;do
   checkpid
   if [ $psid -ne 0 ]; then
      echo -e "warn: \033[30;33m$ServiceName\033[0m already \033[42;37mstarted\033[0m (pid=$psid)"
      echo "================================"
      sleep 0.5
   else
      echo -ne "Starting \033[30;33m$ServiceName\033[0m ..."
      javaopts
      ServiceFileName
      if [ "$JavaServiceName" != "" ];then
          nohup java $JAVA_OPTS -jar $JavaServiceName > /dev/null 2>&1 &
          sleep 5
          checkpid
          if [ $psid -ne 0 ]; then
             echo -e " \033[42;37m[OK]\033[0m (pid=$psid)"
          else
             echo -e "\033[30;31m [Failed]\033[0m"
          fi
      else
          echo "jar package is not found"
      fi
   fi
 done
}

allstop() {
 for ServiceName in $ServiceList;do
   checkpid
   if [ $psid -ne 0 ]; then
      echo -ne "Stopping \033[30;33m$ServiceName\033[0m ...(pid=$psid) "
      kill -9 $psid
      if [ $? -eq 0 ]; then
         echo -e "\033[42;37m[OK]\033[0m"
      else
         echo -e "\033[30;31m[Failed]\033[0m"
      fi
   else
      echo -e "warn: \033[30;33m$ServiceName\033[0m is not running"
      echo "================================"
   fi
   sleep 0.5
 done
}

allstatus() {
 for ServiceName in `echo $ServiceList`;do
   checkpid
   if [ $psid -ne 0 ];  then
      echo -e "\033[30;33m$ServiceName\033[0m is \033[42;37mrunning\033[0m (pid=$psid)"
   else
      echo -e "\033[30;33m$ServiceName\033[0m is \033[30;31mnot running\033[0m"
   fi
   sleep 0.5
 done
}

case "$1" in
   'start')
      start
      ;;
   'stop')
     stop
     ;;
   'restart')
     stop
     sleep 3
     start
     ;;
   'status')
     status
     ;;
   'allstop')
    allstop
     ;;
   'allstart')
    allstart
     ;;
   'allstatus')
    allstatus
     ;;
   'allrestart')
    allstop
    sleep 5
    allstart
     ;;
  *)
     echo "Usage: $0 {start|stop|restart|status ServiceName or allstart|allstop|allstatus|allrestart}"
     exit 1
esac
