#!/bin/bash
PATH=/bin:/usr/bin:/sbin:/usr/sbin
#把本机公钥添加到远程主机即可
adirname() { odir=`pwd`; cd `dirname $1`; pwd; cd "${odir}"; }
MYDIR=`adirname "$0"`
vhosts_dir='/usr/local/nginx/conf/vhosts'
nginx_conf='/usr/local/nginx/conf/nginx.conf'
upstream_file='/usr/local/nginx/conf/upstream.conf'
yum_nginx_conf='/etc/nginx/nginx.conf'
yum_nginx_conf_dir='/etc/nginx/conf.d'

cat $MYDIR/iplist|egrep -v '^#|^$'|while read ipinfo;do
    ip_addr=`echo $ipinfo|awk '{print $1}'`
    # 默认端口为10022
    ip_port=`if [[ -n $(echo $ipinfo|awk '{print $2}') ]];then echo $(echo $ipinfo|awk '{print $2}');else echo 10022;fi`
    # 默认用户为root
    login_user=`if [[ -n $(echo $ipinfo|awk '{print $3}') ]];then echo $(echo $ipinfo|awk '{print $3}');else echo root;fi`
    ssh -o ConnectTimeout=1 -p ${ip_port} $login_user@$ip_addr "if [ -f /usr/local/nginx/sbin/nginx ];then if [ ! -f /usr/local/nginx/conf/vhosts/nginx_configure ];then /usr/local/nginx/sbin/nginx -V >/usr/local/nginx/conf/vhosts/nginx_configure 2>&1;fi;fi" </dev/null
    echo -e "----------------------------------------\n$(date '+%Y-%-m-%d %H:%M') rsync_nginx_config_form $ip_addr to_local\n" >> $MYDIR/rsync.log
    if [ ! -d $MYDIR/$ip_addr ];then mkdir -p $MYDIR/$ip_addr;fi
    for i in $vhosts_dir $nginx_conf $upstream_file $yum_nginx_conf $yum_nginx_conf_dir;do
        rsync -qrt -e "ssh -p ${ip_port}"  --exclude-from=$MYDIR/rsync.exclude --log-file=$MYDIR/rsync.log --progress $login_user@$ip_addr:$i $MYDIR/$ip_addr
    done
done



# cat file iplist 
#如果不是root用户登录，那么必须写端口号
#默认端口为10022，用户为root
#azure-pord
10.0.0.5
#azure-test
10.0.0.6 22 someuser

