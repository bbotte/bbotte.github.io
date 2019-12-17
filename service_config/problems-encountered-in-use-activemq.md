---
layout: default
---

# activemq使用中遇到的问题

1. 说明
2. activemq管理页面使用默认的用户名和密码
3. 服务器磁盘空间不足
4. activemq的一个bug
5. 故障总结
6. activemq集群配置

### 说明

activemq提供消息队列，公司用的是activemq 5.10.0版本，和zookeeper结合dubbo使用。在使用过程中遇到了点问题，记录一下，对自己做一个提醒。activemq集群配置在最后面
<http://activemq.apache.org/>
<http://zookeeper.apache.org/>
<http://dubbo.io/Home-zh.htm>

![activemq使用中遇到的问题 - 第1张](../images/2016/03/activemq_logo.png)

第一次故障原因，

### **activemq管理页面使用默认的用户名和密码**

结果。。。
措施：更改activemq的端口和用户名密码

```
activemq
conf/jetty.xml
        <property name="port" value="8161"/>
 
conf/jetty-realm.properties 
# username: password [,rolename ...]
#admin: admin, admin
#user: user, user
yonghuming: yourpassword ,admin
```

第二次故障，因为

### **服务器磁盘空间不足**

把mongodb和activemq放到一台云主机，并且云主机硬盘空间为100G，mongodb随着时间占用磁盘到40G，activemq又挂了，因此更改几个配置参数

错误日志：

```
2016-01-15 09:50:02,634 | WARN  | Store limit is 102400 mb (current store usage is 200 mb). The data directory: /usr/local/activemq/data/leveldb only has 16630 mb of usable space - resetting to maximum availabl
e disk space: 16830 mb | org.apache.activemq.broker.BrokerService | main
2016-01-15 09:50:02,635 | ERROR | Temporary Store limit is 51200 mb, whilst the temporary data directory: /usr/local/activemq/data/test_mq/tmp_storage only has 16630 mb of usable space - resetting to maximum a
vailable 16630 mb. | org.apache.activemq.broker.BrokerService | main
```

修改配置：

```
# grep -v ^# /usr/local/activemq/conf/activemq.xml |sed '/^$/d'
<beans
  xmlns="http://www.springframework.org/schema/beans"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd
  http://activemq.apache.org/schema/core http://activemq.apache.org/schema/core/activemq-core.xsd">
    <!-- Allows us to use system properties as variables in this configuration file -->
    <bean class="org.springframework.beans.factory.config.PropertyPlaceholderConfigurer">
        <property name="locations">
            <value>file:${activemq.conf}/credentials.properties</value>
        </property>
    </bean>
   <!-- Allows accessing the server log -->
<!--    <bean id="logQuery" class="org.fusesource.insight.log.log4j.Log4jLogQuery"
          lazy-init="false" scope="singleton"
          init-method="start" destroy-method="stop">
    </bean>
-->
    <!--
        The <broker> element is used to configure the ActiveMQ broker.
    -->
    <broker xmlns="http://activemq.apache.org/schema/core" brokerName="your_mq_name" dataDirectory="${activemq.data}"> #名称自己定义
        <destinationPolicy>
            <policyMap>
              <policyEntries>
                <policyEntry topic=">" >
                    <!-- The constantPendingMessageLimitStrategy is used to prevent
                         slow topic consumers to block producers and affect other consumers
                         by limiting the number of messages that are retained
                         For more information, see:
                         http://activemq.apache.org/slow-consumer-handling.html
                    -->
                  <pendingMessageLimitStrategy>
                    <constantPendingMessageLimitStrategy limit="1000"/>
                  </pendingMessageLimitStrategy>
                </policyEntry>
              </policyEntries>
            </policyMap>
        </destinationPolicy>
        <!--
            The managementContext is used to configure how ActiveMQ is exposed in
            JMX. By default, ActiveMQ uses the MBean server that is started by
            the JVM. For more information, see:
            http://activemq.apache.org/jmx.html
        -->
        <managementContext>
            <managementContext createConnector="false"/>
        </managementContext>
        <!--
            Configure message persistence for the broker. The default persistence
            mechanism is the KahaDB store (identified by the kahaDB tag).
            For more information, see:
            http://activemq.apache.org/persistence.html
        -->
        <persistenceAdapter>
        <replicatedLevelDB
        directory="${activemq.data}/leveldb"
        replicas="3"
        bind="tcp://0.0.0.0:0"
        zkAddress="10.117.1.1:2181,10.117.1.2:2181,10.117.1.3:2181"  #zookeeper
        hostname="10.1.1.1"                                          #本机hostname
        sync="local_disk"
        zkPath="/activemq/leveldb-stores"
        />
        </persistenceAdapter>
          <!--
            The systemUsage controls the maximum amount of space the broker will
            use before disabling caching and/or slowing down producers. For more information, see:
            http://activemq.apache.org/producer-flow-control.html
          -->
          <systemUsage>
            <systemUsage>
                <memoryUsage>
                    <memoryUsage percentOfJvmHeap="40" />  #非持久化消息最大占用内存大小
                </memoryUsage>
                <storeUsage>
                    <storeUsage limit="20 gb"/>            #持久化消息最大占用硬盘大小
                </storeUsage>
                <tempUsage>
                    <tempUsage limit="5 gb"/>              #临时消息最大占用硬盘大小
                </tempUsage>
            </systemUsage>
        </systemUsage>
        <!--
            The transport connectors expose ActiveMQ over a given protocol to
            clients and other brokers. For more information, see:
            http://activemq.apache.org/configuring-transports.html
        -->
        <transportConnectors>
            <!-- DOS protection, limit concurrent connections to 1000 and frame size to 100MB maxFrameSize=104857600就是代表100M空间-->
            <transportConnector name="openwire" uri="tcp://0.0.0.0:61616?maximumConnections=1000&wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="amqp" uri="amqp://0.0.0.0:5672?maximumConnections=1000&wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="stomp" uri="stomp://0.0.0.0:61613?maximumConnections=1000&wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="mqtt" uri="mqtt://0.0.0.0:1883?maximumConnections=1000&wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="ws" uri="ws://0.0.0.0:61614?maximumConnections=1000&wireFormat.maxFrameSize=104857600"/>
        </transportConnectors>
        <!-- destroy the spring context on shutdown to stop jetty -->
        <shutdownHooks>
            <bean xmlns="http://www.springframework.org/schema/beans" class="org.apache.activemq.hooks.SpringContextHook" />
        </shutdownHooks>
    </broker>
    <!--
        Enable web consoles, REST and Ajax APIs and demos
        The web consoles requires by default login, you can disable this in the jetty.xml file
        Take a look at ${ACTIVEMQ_HOME}/conf/jetty.xml for more details
    -->
    <import resource="jetty.xml"/>
</beans>
<!-- END SNIPPET: example -->
```

第三次故障是因为

### **activemq的一个bug**

日志如下：

```
2016-03-09 21:10:16,329 | WARN  | [/activemq/leveldb-stores/00000000157] [ZooKeeperTreeTracker@4e51a33] \
[Thread[main-EventThread,5,main]] Error in treeWatcher (ignored) | org.linkedin.zookeeper.tracker.ZooKeeperTreeTracker | main-EventThread
org.apache.zookeeper.KeeperException$ConnectionLossException: KeeperErrorCode = ConnectionLoss for \
 /activemq/leveldb-stores/00000000157
        at org.apache.zookeeper.KeeperException.create(KeeperException.java:99)[zookeeper-3.4.5.jar:3.4.5-1392090]
        at org.apache.zookeeper.KeeperException.create(KeeperException.java:51)[zookeeper-3.4.5.jar:3.4.5-1392090]
        at org.apache.zookeeper.ZooKeeper.getData(ZooKeeper.java:1151)[zookeeper-3.4.5.jar:3.4.5-1392090]
        at org.linkedin.zookeeper.client.ZooKeeperImpl.getData(ZooKeeperImpl.java:191)[org.linkedin.zookeeper-impl-1.4.0.jar:]
        at org.linkedin.zookeeper.client.AbstractZooKeeper.getData(AbstractZooKeeper.java:213)[org.linkedin.zookeeper-impl-1.4.0.jar:]
        at org.linkedin.zookeeper.client.AbstractZKClient.getZKByteData(AbstractZKClient.java:213)[org.linkedin.zookeeper-impl-1.4.0.jar:]
        at org.linkedin.zookeeper.tracker.ZKByteArrayDataReader.readData(ZKByteArrayDataReader.java:37)[org.linkedin.zookeeper-impl-1.4.0.jar:]
        at org.linkedin.zookeeper.tracker.ZooKeeperTreeTracker.trackNode(ZooKeeperTreeTracker.java:280)[org.linkedin.zookeeper-impl-1.4.0.jar:]
        at org.linkedin.zookeeper.tracker.ZooKeeperTreeTracker.handleNodeDataChanged(ZooKeeperTreeTracker.java:369)[org.linkedin.zookeeper-impl-1.4.0.jar:]
        at org.linkedin.zookeeper.tracker.ZooKeeperTreeTracker.access$700(ZooKeeperTreeTracker.java:50)[org.linkedin.zookeeper-impl-1.4.0.jar:]
        at org.linkedin.zookeeper.tracker.ZooKeeperTreeTracker$TreeWatcher.process(ZooKeeperTreeTracker.java:105)[org.linkedin.zookeeper-impl-1.4.0.jar:]
        at org.apache.zookeeper.ClientCnxn$EventThread.processEvent(ClientCnxn.java:519)[zookeeper-3.4.5.jar:3.4.5-1392090]
        at org.apache.zookeeper.ClientCnxn$EventThread.run(ClientCnxn.java:495)[zookeeper-3.4.5.jar:3.4.5-1392090]
```

谷歌得知许多人也同样遇到过，是activemq的一个bug，参考下面链接：

```
http://activemq.2283324.n4.nabble.com/ActiveMQ-Master-Slave-with-ZooKeeper-Session-Expiration-td4686562.html
http://qnalist.com/questions/5326473/activemq-master-slave-with-zookeeper-session-expiration
请复制下链接查看
https://issues.apache.org/jira/browse/AMQ-5082
After about a day or so of sitting idle there are cascading failures and the cluster completely stops 
listening all together.
I can reproduce this consistently on 5.9 and the latest 5.10 
(commit 2360fb859694bacac1e48092e53a56b388e1d2f0). I am going to attach logs from the three mq nodes and 
the zookeeper logs that reflect the time where the cluster starts having issues.
```

![activemq使用中遇到的问题 - 第2张](../images/2016/03/QQ%E5%9B%BE%E7%89%8720160310155301.png)

这个bug在activemq单机模式下不会出现，只有在集群模式，并且安稳运行两周左右凸显，暂时的解决方式是每周在业务量最低的时候重启一次集群，等待新版本的发布

### 故障总结

这三次故障均是activemq进程在，端口关闭，所以监控的话可以从端口入手，及时发现并处理，因此：

线上使用某一个软件之前，
1，和同类软件之间的性能比较
2，了解运行原理
3，配置参数搞明白
4，带着对软件的监控报警上线

附

### activemq集群配置

```
activemq集群依赖zookeeper集群，所以需要先配置zookeeper集群
下载zookeeper安装包，解压即可
# grep -v ^# /usr/local/zookeeper/conf/zoo.cfg
tickTime=2000
initLimit=10
syncLimit=5
dataDir=/tmp/zookeeper
clientPort=2181
server.1=192.168.1.5:2888:3888
server.2=192.168.1.6:2888:3888
server.3=192.168.1.7:2888:3888
 
分别在三台主机手动建立不同的myid，比如1，2，3
# cat /tmp/zookeeper/myid 
1
 
然后启动zookeeper集群
/usr/local/zookeeper/bin/zkServer.sh start
 
下载activemq安装包，并解压
# grep -v ^# /usr/local/activemq/conf/activemq.xml |sed '/^$/d'
<beans
  xmlns="http://www.springframework.org/schema/beans"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd
  http://activemq.apache.org/schema/core http://activemq.apache.org/schema/core/activemq-core.xsd">
    <!-- Allows us to use system properties as variables in this configuration file -->
    <bean class="org.springframework.beans.factory.config.PropertyPlaceholderConfigurer">
        <property name="locations">
            <value>file:${activemq.conf}/credentials.properties</value>
        </property>
    </bean>
   <!-- Allows accessing the server log 请注意 !! 这里注释了，请注意 !!-->
<!--    <bean id="logQuery" class="org.fusesource.insight.log.log4j.Log4jLogQuery"
          lazy-init="false" scope="singleton"
          init-method="start" destroy-method="stop">
    </bean>
-->
    <!--
        The <broker> element is used to configure the ActiveMQ broker.
 请注意 !! 下面一行brokerName一般更改一下，避免多个activemq集群互串，请注意 !!-->
    <broker xmlns="http://activemq.apache.org/schema/core" brokerName="bbotte_mq" dataDirectory="${activemq.data}">
        <destinationPolicy>
            <policyMap>
              <policyEntries>
                <policyEntry topic=">" >
                    <!-- The constantPendingMessageLimitStrategy is used to prevent
                         slow topic consumers to block producers and affect other consumers
                         by limiting the number of messages that are retained
                         For more information, see:
                         http://activemq.apache.org/slow-consumer-handling.html
                    -->
                  <pendingMessageLimitStrategy>
                    <constantPendingMessageLimitStrategy limit="1000"/>
                  </pendingMessageLimitStrategy>
                </policyEntry>
              </policyEntries>
            </policyMap>
        </destinationPolicy>
        <!--
            The managementContext is used to configure how ActiveMQ is exposed in
            JMX. By default, ActiveMQ uses the MBean server that is started by
            the JVM. For more information, see:
            http://activemq.apache.org/jmx.html
        -->
        <managementContext>
            <managementContext createConnector="false"/>
        </managementContext>
        <!--
            Configure message persistence for the broker. The default persistence
            mechanism is the KahaDB store (identified by the kahaDB tag).
            For more information, see:
            http://activemq.apache.org/persistence.html
        -->
        <persistenceAdapter>
        <replicatedLevelDB
         directory="${activemq.data}/leveldb"
          replicas="3"
          bind="tcp://0.0.0.0:0"
          zkAddress="192.168.1.5:2181,192.168.1.6:2181,192.168.1.7:2181"  #zookeeper集群的ip
           hostname="bbotte_1"          #本机hostname
          zkPassword="password"
           sync="local_disk"
           zkPath="/activemq/leveldb-stores"
             />
        </persistenceAdapter>
          <!--
            The systemUsage controls the maximum amount of space the broker will
            use before disabling caching and/or slowing down producers. For more information, see:
            http://activemq.apache.org/producer-flow-control.html
          -->
          <systemUsage>
            <systemUsage>
                <memoryUsage>
                    <memoryUsage percentOfJvmHeap="70" />
                </memoryUsage>
                <storeUsage>
                    <storeUsage limit="10 gb"/>        #这里就不说了，栽过坑
                </storeUsage>
                <tempUsage>
                    <tempUsage limit="5 gb"/>
                </tempUsage>
            </systemUsage>
        </systemUsage>
        <!--
            The transport connectors expose ActiveMQ over a given protocol to
            clients and other brokers. For more information, see:
            http://activemq.apache.org/configuring-transports.html
        -->
        <transportConnectors>
            <!-- DOS protection, limit concurrent connections to 1000 and frame size to 100MB -->
            <transportConnector name="openwire" uri="tcp://0.0.0.0:61616?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="amqp" uri="amqp://0.0.0.0:5672?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="stomp" uri="stomp://0.0.0.0:61613?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="mqtt" uri="mqtt://0.0.0.0:1883?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
            <transportConnector name="ws" uri="ws://0.0.0.0:61614?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
        </transportConnectors>
        <!-- destroy the spring context on shutdown to stop jetty -->
        <shutdownHooks>
            <bean xmlns="http://www.springframework.org/schema/beans" class="org.apache.activemq.hooks.SpringContextHook" />
        </shutdownHooks>
    </broker>
    <!--
        Enable web consoles, REST and Ajax APIs and demos
        The web consoles requires by default login, you can disable this in the jetty.xml file
        Take a look at ${ACTIVEMQ_HOME}/conf/jetty.xml for more details
    -->
    <import resource="jetty.xml"/>
</beans>
<!-- END SNIPPET: example -->
```

```
如果是3台主机的activemq，那么配置文件都用一致的
lib文件夹下移除pax-url-aether-1.5.2.jar
mv /usr/local/activemq/lib/pax-url-aether-1.5.2.jar{,.bak}
 
activemq的配置文件activemq.xml里面，主要是修改这三个方面：
1，注释logQuery
2，brokerName保持一致
3，replicatedLevelDB 这里改动如下
        <persistenceAdapter>
<!--            <kahaDB directory="${activemq.data}/kahadb"/> -->
        <replicatedLevelDB
         directory="${activemq.data}/leveldb"
          replicas="3"
          bind="tcp://0.0.0.0:0"
          zkAddress="192.168.1.5:2181,192.168.1.6:2181,192.168.1.7:2181"
           hostname="bbotte_1"
          zkPassword="password"
           sync="local_disk"
           zkPath="/activemq/leveldb-stores"
             />
        </persistenceAdapter
 
启动
/usr/local/activemq/bin/activemq restart
最后查看zookeeper和activemq的状态
 
/usr/local/zookeeper/bin/zkServer.sh status
/usr/local/activemq/bin/activemq status
lsof -i:8161
lsof -i:61616
```

如果activemq集群故障，比如启动不起来，报种种日志，着急的话修改brokerName马上启动

2016年03月10日 于 [linux工匠](http://www.bbotte.com/) 发表

