#!/bin/bash
#Check MySQL Slave's Runnning Status
PATH=/bin:/usr/bin:/sbin:/usr/sbin
function CheckSlaveStatus() {
        SQL_env=$(mysql -uroot -h 127.0.0.1 -e "show slave status\G" 2>&1| grep -w "Slave_SQL_Running"|awk '{print $2}')
        SQL_errno=$(mysql -uroot -h 127.0.0.1 -e "show slave status\G" 2>&1| grep -w "Last_SQL_Errno"|awk '{print $2}')
}

while true;do
CheckSlaveStatus
if [ "$SQL_env" = "No" ]; then
        echo `date +%m%d-%H:%M:%S` `mysql -uroot -h 127.0.0.1 -e "show slave status\G" | grep -w "Last_SQL_Error"`  >> /tmp/slave_skip_log
NEXTGTID=`mysql -uroot -h 127.0.0.1 -e "select * from performance_schema.replication_applier_status_by_worker where LAST_ERROR_NUMBER=${SQL_errno} \G"|grep LAST_SEEN_TRANSACTION|awk '{print $2}'`
mysql -uroot -h 127.0.0.1 -e "stop slave; set @@session.gtid_next='${NEXTGTID}';begin;commit;set @@session.gtid_next=automatic; start slave;"
fi
sleep 0.5
done
