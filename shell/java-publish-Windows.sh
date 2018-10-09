#!/bin/bash
PATH=/bin:/usr/bin:/sbin:/usr/sbin:/c/Windows/System32:/c/Program\ Files/Git/usr/bin
#windows版本java发布shell，需要安装git bash，默认安装即可
#./startJavaService.sh start/stop/status/restart ServiceName 
#./startJavaService.sh allstart/allstop/allstatus/allrestart
#cat ${ServiceName}Env.sh
#JAVA_OPTS="-server -Xmx2g -Xms2g -Xmn256m"
#cat /d/ServicePort
#8000 system
#8001 task

ServiceName=$2
WORKSPACE="/d/jar"
ServiceList="system task"

base_dir=$(dirname $0)

ServiceFileName() {
    JavaServiceName=
    JavaServiceName=`find ${WORKSPACE} -name "${ServiceName}*.jar"`
}

javaopts() {
    if [ -f "$base_dir/${ServiceName}Env.sh" ]; then
      . "$base_dir/${ServiceName}Env.sh"
    else
      export JAVA_OPTS="-server -Xmx3G -Xms3G -Duser.timezone=GMT+08 -Dfile.encoding=UTF-8"
    fi
}

checkpid() {
    psid=0
	javaps=
    ServerPort=`grep -w ${ServiceName} /d/ServicePort|awk '{print $1}'` 
	if [ -n "$ServerPort" ];then
        WinPid=`netstat -ano|grep -w ${ServerPort}|grep 0.0.0.0|awk '{print $NF}'`
	fi
    if [ -n "$WinPid" ];then	
	    javaps=`ps aux|grep ${WinPid}|awk '{print $1}'`
	fi
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
          nohup.exe /c/ProgramData/Oracle/Java/javapath/java.exe $JAVA_OPTS -jar $JavaServiceName >/dev/null 2>&1 &
          sleep 20
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
      #echo "`date` $ServiceName is not running"|mail -s "Check Service Status is Fail" ${MailArray[*]}
      echo -ne "Starting \033[30;33m$ServiceName\033[0m ..."
      javaopts
      ServiceFileName
	  if [ "$JavaServiceName" != "" ];then
          nohup.exe /c/ProgramData/Oracle/Java/javapath/java.exe $JAVA_OPTS -jar $JavaServiceName >/dev/null 2>&1 &
          sleep 20
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
      if [[ $? -eq 0 ]]; then
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
    sleep 3
    allstart
     ;;
  *)
     echo "Usage: $0 {start|stop|restart|status ServiceName or allstart|allstop|allstatus|allrestart}"
     exit 1
esac
