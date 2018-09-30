如果不需要固定mysql的IP，下面可以不用，并且docker-compose.yml中最下面network需修改
# cat /etc/docker/daemon.json 
{
"bip": "172.17.0.1/24",
"fixed-cidr": "172.17.0.0/24",
"insecure-registries":["harbor.bbotte.com"]
}
docker-compose.yml修改部分
db-com:
    networks:
      bbotte:
        ipv4_address: 172.17.1.100
修改为
db-com:
    networks:
     - bbotte

最下面network修改为
networks:
  bbotte:
    external: false


先把docker服务的版本号写入到ServiceVersion里面，执行
./update.sh 即可完成更新
