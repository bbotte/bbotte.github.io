php-publish.sh
#!/bin/bash
PATH="/bin:/usr/bin:/sbin:/usr/sbin"
adirname() { odir=`pwd`; cd `dirname $1`; pwd; cd "${odir}"; }

MYNAM=`basename "$0"`
MYDIR=`adirname "$0"`
branch=$1
if  [ ! -n "$branch" ] ;then
    echo "Please input deploy staging branch,exit!!!"
    exit;
fi

MYLCK="/tmp/${MYNAM}.lock"

# message - output message on stdout
message() { echo "$@"; }
# die - output message on stderr and exit
die()     { message "$@"; exit 1; }

check_exit()
{
        EXIT=$1
        MSG=$2
        if [ $1 -eq 0 ] ; then
                echo -e "[\e[0;32;1mOK\e[0m]"
        else
                echo -e "[\e[0;31;1mFAIL\e[0m]"
                die "${MSG}"
        fi
}

cfg="${MYDIR}/host.config"
[ ! -f "$cfg" ] && die "Error: Missing configuration file - $cfg!"
source "$cfg"

[ ! -d "${BASEDIR}" ] && die "Error: Missing echo base directory - ${BASEDIR}!"

# check locking
[ -s "${MYLCK}" ] && kill -0 `cat "${MYLCK}"` 2>/dev/null &&
die "${MYNAM}: already running!"
echo "$$" > "${MYLCK}"

#RSYNC_OPTION="--delete -avzl --force"
RSYNC_OPTION="-avl --delete-after --force --exclude=runtime"
[ -f "${EXCLUDE_PROD}" ] && RSYNC_OPTION="${OPTION} --exclude-from=${EXCLUDE_PROD}"

DATE=`date +%Y%m%d_%H%M%S`

> ${LOG_SYNC_PROD}

echo "please provide your name as deployer: ... "
read deployer

NODES=($NODES)

command="mkdir -p /data/webroot/$branch/current"
child_pids=()
for (( i = 0; i < ${#NODES[@]}; ++i )); do
        NODE=${NODES[$i]}
       	NODE_NAME=$(echo $NODE | cut -f1 -d:);
        NODE_IP=$(echo $NODE | cut -f2 -d:);
        {
                echo "cloning directory on ${NODE_NAME} [ $NODE_IP ] and then rsync files to [ $NODE_IP ] in background";
                ssh -p10022 root@${NODE_IP} "$command" < /dev/null && rsync ${RSYNC_OPTION} ${BASEDIR}/ rsync://${NODE_IP}/api/$branch/current >> ${LOG_SYNC_PROD} 2>&1 < /dev/null;
        }
        child_pids=("${child_pids[@]}" "$!");
done

for NODE in "${NODES[@]}"; do
        NODE_NAME=$(echo $NODE | cut -f1 -d:)
        NODE_IP=$(echo $NODE | cut -f2 -d:)
echo -n "Prepare folder structure for ${DATE} on ${NODE_NAME} [ ${NODE_IP} ] ... "
ssh -p10022 root@${NODE_IP} "cd /data/webroot/$branch/current &&  mkdir -p runtime && mkdir -p runtime/cache && chmod -R 777 runtime && rm -rf runtime/cache/*"
        check_exit $? "Error: Failed to prepare folders for ${NODE_NAME}, please contact a sysadmin!"

        echo -n "Restart php-fpm on ${NODE_NAME} [ ${NODE_IP} ] ... "
ssh -p10022 root@$NODE_IP "/etc/init.d/php-fpm reload >/dev/null 2>&1"
        check_exit $? "Error: Failed to reload php-fpm on ${NODE_NAME}, please contact a sysadmin!"
done

echo "${DATE} by ${deployer}" >> ${MYDIR}/versions
echo ""
echo "Finished deploying [ ${DATE} ]! $$$$"

rm -f "${MYLCK}"



#文件 host.config
BASEDIR=/data/pub
LOG_SYNC_PROD=/data/log
NODES:[ test: 192.168.1.1 192.168.1.2 foo: 172.16.1.1 ]

#执行发布
#sh php-publish.sh dev
#username
