# 查看本机运行的java服务端口
for i in `jps|egrep -v "Bootstrap|Jps"|awk '{print $1}'`;do netstat -tnlp|grep $i|awk '{print $4}'|awk -F':' '{print $4}';ps aux |grep $i |awk '{print $17}'|awk -F'/' '{print $NF}'|awk -F'-' '{print $1}';echo ----- ;done
