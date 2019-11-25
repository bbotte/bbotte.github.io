# kubernetes集群中的kafka服务配置

kubernetes集群中的kafka服务配置

zookeeper Dockerfile  <https://github.com/31z4/zookeeper-docker/tree/master/3.5.6>

kafka Dockerfile  <https://github.com/bbotte/bbotte.github.io/tree/master/Commonly-Dockerfile/kafka-cluster>

如果是单机跑kafka服务，那么用docker-compose更方便，配置如下：

```
version: '2.4'
services:
  zookeeper-com:
    container_name: zookeeper-com
    image: zookeeper   #zookeeper image: https://github.com/31z4/zookeeper-docker/tree/master/3.5.6
    ports:
     - 2181:2181
    networks:
     - bbotte
    environment:
      ZOO_MY_ID: "1"
      ZOO_SERVERS: "server.1=0.0.0.0:2888:3888;2181 "
 
  kafka-com:
    container_name: kafka-com
    image: kafka:0.1
    ports:
     - 9092:9092
     - 9094:9094
    networks:
     - bbotte
    environment:
      KAFKA_BROKER_ID: "1"
      KAFKA_CREATE_TOPICS: "test:1:1"
      KAFKA_ZOOKEEPER_CONNECT: "zookeeper-com:2181"
      KAFKA_ADVERTISED_LISTENERS: "INSIDE://:9092,OUTSIDE://kafka-com:9094"
      KAFKA_LISTENERS: "INSIDE://:9092,OUTSIDE://:9094"
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: "INSIDE:PLAINTEXT,OUTSIDE:PLAINTEXT"
      KAFKA_INTER_BROKER_LISTENER_NAME: "INSIDE"
 
networks:
  bbotte:
    external: false
```

```
cd kafka_2.12-2.3.0/bin/
./kafka-topics.sh --create --bootstrap-server kafka-com:9094 --replication-factor 1 --partitions 1  --topic test
./kafka-topics.sh --list --bootstrap-server kafka-com:9094
 
./kafka-console-producer.sh --broker-list kafka-com:9094 --topic test
./kafka-console-consumer.sh --bootstrap-server kafka-com:9094 --topic test --from-beginning
```

连接kafka-com需要dns解析到这台docker-compose主机，简单的方式为添加hosts即可测试。下面说一下在kubernetes中的配置

```
# cat kafka.yaml
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: kafka
  namespace: dev
  labels:
    k8s-app: kafka
spec:
  replicas: 1
  revisionHistoryLimit: 1
  minReadySeconds: 10
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      k8s-app: kafka
  template:
    metadata:
      labels:
        k8s-app: kafka
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values:
                - k8sn1
      containers:
      - name: kafka
        imagePullPolicy: IfNotPresent
        image: kafka:0.1
        resources:
          limits:
            memory: "2Gi"
          requests:
            memory: "0.1Gi"
            cpu: "0.1"
        ports:
        - containerPort: 9092
        #- containerPort: 9094
        - containerPort: 30322
        env:
        - name: KAFKA_BROKER_ID
          value: "1"
        - name: KAFKA_CREATE_TOPICS
          value: "test:1:1"
        - name: KAFKA_ZOOKEEPER_CONNECT
          value: "zookeeper-com:2181"
        - name: KAFKA_ADVERTISED_LISTENERS
          #value: "INSIDE://:9092,OUTSIDE://kafka-com:9094"
          value: "INSIDE://:9092,OUTSIDE://kafka-com:30322"
        - name: KAFKA_LISTENERS
          #value: "INSIDE://:9092,OUTSIDE://:9094"
          value: "INSIDE://:9092,OUTSIDE://:30322"
        - name: KAFKA_LISTENER_SECURITY_PROTOCOL_MAP
          value: "INSIDE:PLAINTEXT,OUTSIDE:PLAINTEXT"
        - name: KAFKA_INTER_BROKER_LISTENER_NAME
          value: "INSIDE" 
 
        volumeMounts:
        - name: kafka-data
          mountPath: /data
      volumes:
      - name: kafka-data
        persistentVolumeClaim:
          claimName: gfsdev
      imagePullSecrets:
      - name: harbor-auth-dev
 
---
kind: Service
apiVersion: v1
metadata:
  name: kafka-com
  namespace: dev
  labels:
    k8s-app: kafka
spec:
  selector:
    k8s-app: kafka
  ports:
  - port: 9092
    name: innerport
    targetPort: 9092
    protocol: TCP
  #- port: 9094
  #  name: outport 
  #  targetPort: 9094
  #  protocol: TCP
  - port: 30322
    name: outport 
    targetPort: 30322
    protocol: TCP
    nodePort: 30322
  type: NodePort
```

上面有几行前面加#注释的，如果服务只是在k8s内部调用的话，用9094端口即可，不用另外开nodeport。如果在k8s集群内部和外部请求，那么需要保证nodeport和kafka OUTSIDE的端口一致，

```
# cd kafka_2.11-2.3.0/bin/
# ./kafka-topics.sh --list --bootstrap-server kafka-com:30322
test
# ./kafka-console-producer.sh --broker-list kafka-com:30322 --topic test
>hello123
>345
>^C
# 
# ./kafka-console-consumer.sh --bootstrap-server kafka-com:30322 --topic test --from-beginning
^CProcessed a total of 0 messages
# ./kafka-console-consumer.sh --bootstrap-server kafka-com:30322 --topic test --from-beginning --partition 0
hello123
345
^CProcessed a total of 2 messages
```

需要注意的是kafka-console-consumer.sh 没有partition参数的话，不能获取到messages [consumer-not-receiving-messages-kafka-console-new-consumer-api-kafka-0-9](https://stackoverflow.com/questions/34844209/consumer-not-receiving-messages-kafka-console-new-consumer-api-kafka-0-9) ,需要添加 --partition 0参数，然而docker-compose方式不用，主机直接运行kafka没有kubernetes平台也不用此参数

kafka集群没什么特别的，一般用到StatefulSet，存储可以参考[redis cluster](https://github.com/bbotte/bbotte.github.io/blob/master/service_config/redis-cluster/)

kafka集群在kubernetes中的配置 [kubernetes中配置kafka集群](https://github.com/bbotte/bbotte.github.io/tree/master/Commonly-Dockerfile/kafka-cluster)















