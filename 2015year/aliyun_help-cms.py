from aliyunsdkcore import client
from aliyunsdkcms.request.v20151020 import QueryMetricRequest
import datetime

def getEcsMetric(clt,startTimeStr):
        request = QueryMetricRequest.QueryMetricRequest()
        request.set_accept_format('json')
        request.set_Project('acs_ecs')
        #metric reference https://help.aliyun.com/document_detail/cms/API_References/Preset_Metric_Item_Reference.html?spm=5176.775973985.6.133.cb2ZA6
        request.set_Metric('CPUUtilization')
        request.set_StartTime(startTimeStr)
        request.set_Dimensions("{userId:'$your_aliuid', instanceId:'$your_ecs_instanceId'}")
        result = clt.do_action(request)
        print "-----------------------------------"
        print result

def getRdsMetric(clt,startTimeStr):
        request = QueryMetricRequest.QueryMetricRequest()
        request.set_accept_format('json')
        request.set_Project('acs_rds')
        #metric reference https://help.aliyun.com/document_detail/cms/API_References/Preset_Metric_Item_Reference.html?spm=5176.775973985.6.133.cb2ZA6
        request.set_Metric('CpuUsage')
        request.set_StartTime(startTimeStr)
        request.set_Dimensions("{instanceId:'$your_rds_instanceId'}")
        result = clt.do_action(request)
        print "-----------------------------------"
        print result

def main():

		#目前数据是集中的，都在杭州，因此region只能写cn-hangzhou
        clt = client.AcsClient('$your_sercetid','$your_secretkey','cn-hangzhou')
        #query last hour metric
        startTime=datetime.datetime.now() - datetime.timedelta(hours=1)
        startTimeStr=startTime.strftime("%Y-%m-%d %H:%M:%S")
        print startTimeStr

        getEcsMetric(clt, startTimeStr);
        getRdsMetric(clt, startTimeStr);


if __name__ == '__main__':
    main()
