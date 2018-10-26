FROM centos:centos7
COPY mysql57-community-release-el7-11.noarch.rpm /mysql57-community.rpm
#https://dev.mysql.com/get/mysql57-community-release-el7-11.noarch.rpm
RUN yum install -y epel-release && \
    rpm -ivh /mysql57-community.rpm && \
    yum list mysql-community-server --showduplicates && \
    rm -f /etc/localtime && \
    ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    yum remove -y mariadb-libs mariadb-libs && \
    yum install mysql-community-server-5.7.21-1.el7 -y && \
    yum clean all && \
    rm -rf /usr/sbin/mysqld-debug \
    /usr/bin/mysql_config_editor \
    /usr/bin/mysql_ssl_rsa_setup \
    /usr/bin/mysql_upgrade \
    /usr/bin/mysqlslap \
    /usr/bin/mysqlpump \
    /usr/bin/myisam* \
    /usr/lib64/mysql/mecab \
    /usr/lib64/mysql/plugin/debug \
	/usr/lib64/mysql/plugin/mysqlx.so

ADD my.cnf /etc/my.cnf

VOLUME /var/lib/mysql
WORKDIR /

COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

EXPOSE 3306
CMD ["mysqld"]
