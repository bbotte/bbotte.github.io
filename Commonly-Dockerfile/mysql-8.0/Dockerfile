FROM centos:centos7
COPY mysql-community.repo /etc/yum.repos.d/mysql-community.repo
#COPY CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo
#https://mirror.tuna.tsinghua.edu.cn/help/mysql/
#https://dev.mysql.com/get/mysql57-community-release-el7-11.noarch.rpm
RUN yum makecache && \
    yum install -y epel-release && \
    yum list mysql-community-server --showduplicates && \
    rm -f /etc/localtime && \
    ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    rpm --import https://repo.mysql.com/RPM-GPG-KEY-mysql && \
    rpm --import https://repo.mysql.com/RPM-GPG-KEY-mysql-2022 && \
    yum remove -y mariadb-libs mariadb-libs && \
    yum install mysql-community-server-8.0.35-1.el7 -y && \
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

VOLUME /var/lib/mysql
WORKDIR /
RUN mkdir -p /etc/mysql
COPY my.cnf /etc/mysql/my.cnf

COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

EXPOSE 3306
CMD ["mysqld","--defaults-file=/etc/mysql/my.cnf"]
