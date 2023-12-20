#!/bin/bash
#set -xe
set -e
shopt -s nullglob

file_env() {
  local var="$1"
  local fileVar="${var}_FILE"
  local def="${2:-}"
  if [ "${!var:-}" ] && [ "${!fileVar:-}" ]; then
  	echo >&2 "error: both $var and $fileVar are set (but are exclusive)"
  	exit 1
  fi
  local val="$def"
  if [ "${!var:-}" ]; then
  	val="${!var}"
  elif [ "${!fileVar:-}" ]; then
  	val="$(< "${!fileVar}")"
  fi
  export "$var"="$val"
  unset "$fileVar"
}

if [ "$1" = 'mysqld' ]; then
    file_env 'MYSQL_INNODB_BUFFER_POOL_SIZE'
    if [ "$MYSQL_INNODB_BUFFER_POOL_SIZE" ];then
        sed -i "s#innodb_buffer_pool_size=1G#innodb_buffer_pool_size=$MYSQL_INNODB_BUFFER_POOL_SIZE#" /etc/mysql/my.cnf
        echo "MYSQL_INNODB_BUFFER_POOL_SIZE is $MYSQL_INNODB_BUFFER_POOL_SIZE"
    else
        echo "MYSQL_INNODB_BUFFER_POOL_SIZE is 1G"
    fi
    file_env 'MYSQL_INNODB_THREAD_CONCURRENCY'
    if [ "$MYSQL_INNODB_THREAD_CONCURRENCY" ];then
        sed -i "s#innodb_thread_concurrency=8#innodb_thread_concurrency=$MYSQL_INNODB_THREAD_CONCURRENCY#" /etc/mysql/my.cnf
        echo "MYSQL_INNODB_THREAD_CONCURRENCY is $MYSQL_INNODB_THREAD_CONCURRENCY"
    else
        echo "MYSQL_INNODB_THREAD_CONCURRENCY is 8"
    fi
    file_env 'MYSQL_SERVER_ID'
    if [ "$MYSQL_SERVER_ID" ];then
        sed -i "s#server-id=1#server-id=$MYSQL_SERVER_ID#" /etc/mysql/my.cnf
        if [ -z $(grep "read_only=1" /etc/mysql/my.cnf) ];then sed -i "/\[mysqld\]/aread_only=1" /etc/mysql/my.cnf;fi
        echo "MYSQL_SERVER_ID is $MYSQL_SERVER_ID"
    else
        echo "MYSQL_SERVER_ID is 1"
    fi
fi

if [ "$1" = 'mysqld' ]; then
    dataDir=`grep datadir /etc/mysql/my.cnf|awk -F'=' '{print $2}'|xargs dirname`
    if [ "$DATADIR" ] && [ $dataDir != "$DATADIR" ];then
        sed -i "s#$dataDir#$DATADIR#g" /etc/mysql/my.cnf
        mkdir -p $DATADIR/{data,log}
        chown -R mysql.mysql $DATADIR
        echo "mysql data dir is $DATADIR"
    else
        mkdir -p /var/lib/mysql/{data,log} && chown -R mysql.mysql /var/lib/mysql
        echo "mysql data dir is /var/lib/mysql"
    fi
    if [ ! -d "$DATADIR/data/mysql" ] && [ ! -d "/var/lib/mysql/data/mysql" ]; then
        file_env 'MYSQL_ROOT_PASSWORD'
        if [ -z "$MYSQL_ROOT_PASSWORD" -a -z "$MYSQL_ALLOW_EMPTY_PASSWORD" -a -z "$MYSQL_RANDOM_ROOT_PASSWORD" ]; then
        	echo >&2 'error: database is uninitialized and password option is not specified '
        	echo >&2 '  You need to specify one of MYSQL_ROOT_PASSWORD, MYSQL_ALLOW_EMPTY_PASSWORD and MYSQL_RANDOM_ROOT_PASSWORD'
        	exit 1
        fi
        
        echo 'Initializing database'
        "$@" --lower-case-table-names=1 --skip-symbolic-links --initialize-insecure
        echo 'Database initialized, cnf file is /etc/mysql/my.cnf'
  
        SOCKET="/var/lib/mysql/mysql.sock"
        "$@" --skip-networking --socket="${SOCKET}" &
        pid="$!"
        sleep 2
        
        mysql=( mysql -uroot -hlocalhost -S "${SOCKET}" )
        
        for i in {10..0}; do
        	if echo 'SELECT 1' | "${mysql[@]}" &> /dev/null; then
        		break
        	fi
        	echo 'MySQL init process in progress...'
        	sleep 1
        done
        if [ "$i" = 0 ]; then
        	echo >&2 'MySQL init process failed.'
        	exit 1
        fi
        
        if [ ! -z "$MYSQL_RANDOM_ROOT_PASSWORD" ]; then
        	export MYSQL_ROOT_PASSWORD="$(tr -dc '.;_A-Za-z0-9' </dev/urandom | head -c 20)"
        	echo "GENERATED ROOT PASSWORD: $MYSQL_ROOT_PASSWORD"
        fi
        
        rootCreate=
        # default root to listen for connections from anywhere
        file_env 'MYSQL_ROOT_HOST' '%'
        if [ ! -z "$MYSQL_ROOT_HOST" -a "$MYSQL_ROOT_HOST" != 'localhost' ]; then
        	# no, we don't care if read finds a terminating character in this heredoc
        	# https://unix.stackexchange.com/questions/265149/why-is-set-o-errexit-breaking-this-read-heredoc-expression/265151#265151
              read -r -d '' rootCreate <<-EOSQL || true
CREATE USER 'root'@'${MYSQL_ROOT_HOST}' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD}' ;
GRANT ALL ON *.* TO 'root'@'${MYSQL_ROOT_HOST}' WITH GRANT OPTION ;
EOSQL
        fi
        
        "${mysql[@]}" <<-EOSQL
UPDATE mysql.user SET authentication_string="${MYSQL_ROOT_PASSWORD}" WHERE user="root";
${rootCreate}
DROP DATABASE IF EXISTS test ;
FLUSH PRIVILEGES ;
SELECT user, authentication_string FROM mysql.user;
EOSQL
        
        if [ ! -z "$MYSQL_ROOT_PASSWORD" ]; then
        	mysql+=( -p"${MYSQL_ROOT_PASSWORD}" )
        fi
        
        file_env 'MYSQL_DATABASE'
        if [ "$MYSQL_DATABASE" ]; then
        	echo "CREATE DATABASE IF NOT EXISTS \`$MYSQL_DATABASE\` ;" | "${mysql[@]}"
        	mysql+=( "$MYSQL_DATABASE" )
        fi
        
        file_env 'MYSQL_USER'
        file_env 'MYSQL_PASSWORD'
        if [ "$MYSQL_USER" -a "$MYSQL_PASSWORD" ]; then
        	echo "CREATE USER '$MYSQL_USER'@'%' IDENTIFIED BY '$MYSQL_PASSWORD' ;" | "${mysql[@]}"
        
        	if [ "$MYSQL_DATABASE" ]; then
        		echo "GRANT ALL ON \`$MYSQL_DATABASE\`.* TO '$MYSQL_USER'@'%' ;" | "${mysql[@]}"
        	fi
        
        	echo 'FLUSH PRIVILEGES ;' | "${mysql[@]}"
        fi
        
        if [ ! -z "$MYSQL_ONETIME_PASSWORD" ]; then
        	"${mysql[@]}" <<-EOSQL
  ALTER USER "root"@"%" PASSWORD EXPIRE NEVER;
EOSQL
        fi
        if ! kill -s TERM "$pid" || ! wait "$pid"; then
        	echo >&2 'MySQL init process failed.'
        	exit 1
        fi
        
            echo "root passwd is $MYSQL_ROOT_PASSWORD"
        echo
        echo 'MySQL init process done. Ready for start up.'
        echo
    fi
fi

exec "$@" 
