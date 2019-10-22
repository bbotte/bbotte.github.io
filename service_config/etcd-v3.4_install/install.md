#### install etcd 3.4

etcd cluster config file is **etcd.conf.yml.cluster**, and standalone mode config is **etcd.conf.yml.single**

```
mkdir /etc/etcd/
cp etcd.conf.yml.cluster /etc/etcd/etcd.conf.yml
cp etcd etcdctl /usr/bin/
mod +x /usr/bin/etcd*
cp etcd.service /usr/lib/systemd/system/etcd.service

mkdir /var/lib/etcd
chmod 700 /var/lib/etcd
getent group etcd >/dev/null || groupadd -r etcd
getent passwd etcd >/dev/null || useradd -r -g etcd -d /var/lib/etcd -s /sbin/nologin -c "etcd user" etcd
chown etcd.etcd -R /var/lib/etcd/
systemctl daemon-reload
systemctl enable etcd
systemctl start etcd
```

