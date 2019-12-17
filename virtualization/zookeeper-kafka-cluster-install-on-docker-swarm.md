---
layout: default
---

# swarm中的zookeeper和kafka集群配置

docker安装完毕后，需要初始化swarm，swarm的节点分manager和worker，manager具有投票选举、调度服务功能，并且manager可降级为worker节点，反之亦然。manager节点包含worker节点功能，所以服务运行在manager节点没问题。swarm包含etcd数据库和traefik代理，是个mini k8s工具

```
docker swarm init

docker swarm join-token worker
docker swarm join-token manager

docker node ls
docker service ls
```

zookeeper和kafka配置如下：

```
version: '3.7'
services:
  zookeeper1:
    container_name: zookeeper1   # https://github.com/31z4/zookeeper-docker/tree/master/3.5.6
    image: zookeeper
    hostname: zookeeper1
    ports:
     - 2181:2181
    networks:
     - bbotte
    environment:
      ZOO_MY_ID: "1"
      ZOO_SERVERS: "server.1=0.0.0.0:2888:3888;2181 server.2=zookeeper2:2888:3888;2181 server.3=zookeeper3:2888:3888;2181"
      ZOO_DATA_DIR: "/data/"
    volumes:
      - /opt/zk/1/:/data
    deploy:
      replicas: 1
      placement:
        constraints: [node.hostname == vm1]
      resources:
        limits:
          memory: 1024M
  zookeeper2:
    container_name: zookeeper2
    image: zookeeper
    hostname: zookeeper2
    ports:
     - 2182:2181
    networks:
     - bbotte
    environment:
      ZOO_MY_ID: "2"
      ZOO_SERVERS: "server.1=zookeeper1:2888:3888;2181 server.2=0.0.0.0:2888:3888;2181 server.3=zookeeper3:2888:3888;2181"
      ZOO_DATA_DIR: "/data/"
    volumes:
      - /opt/zk/2/:/data
    deploy:
      replicas: 1
      placement:
        constraints: [node.hostname == vm2]
      resources:
        limits:
          memory: 1024M
  zookeeper3:
    container_name: zookeeper3
    image: zookeeper
    hostname: zookeeper3
    ports:
     - 2183:2181
    networks:
     - bbotte
    environment:
      ZOO_MY_ID: "3"
      ZOO_SERVERS: "server.1=zookeeper1:2888:3888;2181 server.2=zookeeper2:2888:3888;2181 server.3=0.0.0.0:2888:3888;2181"
      ZOO_DATA_DIR: "/data/"
    volumes:
      - /opt/zk/3/:/data
    deploy:
      replicas: 1
      placement:
        constraints: [node.hostname == vm3]
      resources:
        limits:
          memory: 1024M
  kafka1:
    container_name: kafka1
    image: kafka   # https://github.com/bbotte/bbotte.github.io/tree/master/Commonly-Dockerfile/kafka
    hostname: kafka1
    ports:
     - 9092:9092
    networks:
     - bbotte
    environment:
      KAFKA_BROKER_ID: "1"
      KAFKA_CREATE_TOPICS: "test:3:3"
      KAFKA_ZOOKEEPER_CONNECT: "zookeeper1:2181,zookeeper2:2182,zookeeper3:2183"
      KAFKA_ADVERTISED_HOST_NAME: "kafka1"
    volumes:
      - /opt/kafka/1/:/data
    depends_on:
      - zookeeper1
    deploy:
      replicas: 1
      placement:
        constraints: [node.hostname == vm1]
      resources:
        limits:
          memory: 1024M
  kafka2:
    container_name: kafka2
    image: kafka
    hostname: kafka2
    ports:
     - 9093:9092
    networks:
     - bbotte
    environment:
      KAFKA_BROKER_ID: "2"
      KAFKA_CREATE_TOPICS: "test:3:3"
      KAFKA_ZOOKEEPER_CONNECT: "zookeeper1:2181,zookeeper2:2182,zookeeper3:2183"
      KAFKA_ADVERTISED_HOST_NAME: "kafka2"
    volumes:
      - /opt/kafka/2/:/data
    depends_on:
      - zookeeper2
    deploy:
      replicas: 1
      placement:
        constraints: [node.hostname == vm2]
      resources:
        limits:
          memory: 1024M
  kafka3:
    container_name: kafka3
    image: kafka
    hostname: kafka3
    ports:
     - 9094:9092
    networks:
     - bbotte
    environment:
      KAFKA_BROKER_ID: "3"
      KAFKA_CREATE_TOPICS: "test:3:3"
      KAFKA_ZOOKEEPER_CONNECT: "zookeeper1:2181,zookeeper2:2182,zookeeper3:2183"
      KAFKA_ADVERTISED_HOST_NAME: "kafka3"
    volumes:
      - /opt/kafka/3/:/data
    depends_on:
      - zookeeper3
    deploy:
      replicas: 1
      placement:
        constraints: [node.hostname == vm3]
      resources:
        limits:
          memory: 1024M

  system-com:
    container_name: system-com
    image: harbor.bbotte.com/dev/system:dev-20191126153351-8687cc91
    volumes:
     - /opt/log:/opt/log
    ports:
     - 3005:3005
    networks:
     - bbotte
    deploy:
      mode: global
      update_config:
        parallelism: 2
        delay: 20s
      resources:
        limits:
          memory: 1024M
    healthcheck:
      test: curl -sqf http://127.0.0.1:3005/health/check || exit 1
      interval: 20s
      timeout: 5s
      retries: 3
      
networks:
  bbotte:
    external: false
```

启动并查看服务，docker stack deploy 最后面名称是namespace，服务之间调用可以用bbotte_kafka1,也可用上面配置文件定义服务名称kafka1

```
第一次部署
docker stack deploy --compose-file docker-compose.yml bbotte

更新服务
docker service update bbotte_kafka1 --image XXXX

docker stack up --compose-file docker-compose.yml bbotte

docker stack services bbotte
docker service ps bbotte_kafka1
docker stack ps bbotte

docker service rm bbotte_kafka1
```

验证，到kafka目录

```
./kafka-topics.sh --list --bootstrap-server kafka1:9092
./kafka-console-producer.sh --broker-list kafka1:9092 --topic test
./kafka-console-consumer.sh --bootstrap-server kafka1:9092 --topic test --from-beginning
```

swarm文档

https://docs.docker.com/compose/compose-file/
https://docs.docker.com/engine/reference/commandline/stack/
https://docs.docker.com/engine/swarm/































