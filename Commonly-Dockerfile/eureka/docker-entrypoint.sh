#!/bin/sh
LOG_DIR=/var/log
EUREKALOG=${LOG_DIR}/eureka.log
mkdir -pv $LOG_DIR
touch $EUREKALOG

postFix="svc.cluster.local"
# 向注册中心注册自己
BOOL_REGISTER="true"
# 自己端就是注册中心
BOOL_FETCH="true"

if [ ! -n "$EUREKA_REPLICAS" ]; then EUREKA_REPLICAS=1 ;fi

# 根据副本数进行相关设置
if [ $EUREKA_REPLICAS -eq 1 ]; then
    export EUREKA_URL_LIST="http://$MY_POD_NAME.$MY_IN_SERVICE_NAME:$EUREKA_SERVER_PORT/eureka/,"
    echo " Set the EUREKA_URL_LIST is $EUREKA_URL_LIST" | tee -a $EUREKALOG
else
    tmp=`expr $EUREKA_REPLICAS - 1`
    for i in `seq 0 $tmp `;do
        temp="http://$EUREKA_APPLICATION_NAME-$i.$MY_IN_SERVICE_NAME:$EUREKA_SERVER_PORT/eureka/,"
        EUREKA_URL_LIST="$EUREKA_URL_LIST$temp"
    done
    echo "Set the EUREKA_URL_LIST is ${EUREKA_URL_LIST%?}"  | tee -a $EUREKALOG
fi

#去除结尾的逗号
export EUREKA_URL_LIST=${EUREKA_URL_LIST%?}

echo "MY_NODE_NAME=$MY_NODE_NAME" >> $EUREKALOG
echo "MY_POD_NAME=$MY_POD_NAME" >> $EUREKALOG
echo "MY_POD_NAMESPACE=$MY_POD_NAMESPACE" >> $EUREKALOG
echo "MY_POD_IP=$MY_POD_IP" >> $EUREKALOG
echo "MY_IN_SERVICE_NAME=$MY_IN_SERVICE_NAME" >> $EUREKALOG
echo "EUREKA_APPLICATION_NAME=$EUREKA_APPLICATION_NAME" >> $EUREKALOG
echo "EUREKA_REPLICAS=$EUREKA_REPLICAS" >> $EUREKALOG
echo "EUREKA_URL_LIST=$EUREKA_URL_LIST" >> $EUREKALOG

echo "Start jar...."
java -server -Duser.timezone=GMT+08 $JAVA_OPTIONS -Xmn256m -Xss256k -jar /app.jar
