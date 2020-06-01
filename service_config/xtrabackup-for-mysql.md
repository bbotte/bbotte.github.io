xtrabackup  backup

数据目录大于1G开启增量备份，每周一、周四备份，shell加crontab

```
# cat /opt/shell/xtrabk.sh 
#!/bin/bash
today=`date +%F`
yesterday=`date -d yesterday +%F`
sqlsize=`du -sh /data/bak/xtra*|tail -n 5|awk '{print $1}'|grep -o [[:alpha:]]|grep G`
sqlparameter="--defaults-file=/opt/shell/my.cnf -piris-DB_COM -H127.0.0.1 -uroot"
mkdir /data/bak/xtra${today}
allBak(){
    xtrabackup $sqlparameter --backup --target-dir=/data/bak/xtra${today} 2>> /tmp/xtra.log
}
appendBak(){
    xtrabackup $sqlparameter --backup --target-dir=/data/bak/xtra${today} --incremental-basedir=/data/bak/xtra${yesterday} 2>> /tmp/xtra.log
}
if [[ -z $sqlsize ]];then
    allBak
elif [[ $sqlsize ]] && [[ `date +%w` == 1 || `date +%w` == 4 ]];then
    allBak
else
    appendBak    
fi

# full restore
#systemctl stop mysqld
#xtrabackup $sqlparameter --prepare --target-dir=/data/bak/full_backup_dir
#xtrabackup $sqlparameter --copy-back --target-dir=/data/bak/full_backup_dir 
#chown -R mysql.mysql /var/lib/mysql/
#systemctl start mysqld

# incremental restore
#systemctl stop mysqld
#xtrabackup $sqlparameter --prepare --apply-log-only --target-dir=full_backup_dir
#xtrabackup $sqlparameter --prepare --apply-log-only --target-dir=full_backup_dir --incremental-dir=today_before_yesterday_dir
#xtrabackup $sqlparameter --prepare --apply-log-only --target-dir=full_backup_dir --incremental-dir=yesterday_dir
#xtrabackup $sqlparameter --prepare --apply-log-only --target-dir=full_backup_dir --incremental-dir=today_dir
#xtrabackup $sqlparameter --copy-back --target-dir=/data/bak/full_backup_dir 
#chown -R mysql.mysql /var/lib/mysql/
#systemctl start mysqld

```



文档

[xtrabackup  incremental backup](https://www.percona.com/doc/percona-xtrabackup/2.4/backup_scenarios/incremental_backup.html)