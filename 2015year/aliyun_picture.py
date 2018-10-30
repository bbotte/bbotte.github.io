#!/usr/bin/env python
#ecoding=utf8
#pip install aliyun-python-sdk-ecs  
#pip install aliyun-python-sdk-cms==3.0.5
#
import datetime
import json
import pygal
from aliyunsdkcore import client
from aliyunsdkcms.request.v20151020 import QueryMetricRequest

uid="***"
key="***"
userid = "1234567890"
txt_t = []
txt_content = []
txt_id = ""
metric = "CPUUtilization"
instanceid = '***'

def getEcsMetric(metric, uid, key, userid, instanceid):
    clt = client.AcsClient(uid,key,'cn-qingdao')
    startTime=datetime.datetime.now() - datetime.timedelta(hours=1)
    startTimeStr=startTime.strftime("%Y-%m-%d %H:%M:%S")
    request = QueryMetricRequest.QueryMetricRequest()
    request.set_accept_format('json')
    request.set_Project('acs_ecs')
    request.set_Metric(metric)
    request.set_StartTime(startTimeStr)
    request.set_Dimensions("{userId:'%s', instanceId:'%s'}" % (userid,instanceid))
    ret = clt.do_action(request)
    print(ret)
    data_json = json.loads(ret)
    rawdata = data_json["Datapoints"]["Datapoint"]
    for i in range(len(rawdata)):
        formatdata = (str(rawdata[i]["timestamp"]))[:10]
        txt_time = datetime.datetime.fromtimestamp(int(formatdata)).strftime('%Y-%m-%d %H:%M:%S')
        txt_t.append(txt_time)
        txt_content.append(rawdata[i]["Average"])
        txt_id = '%s' % (instanceid)

    line_chart = pygal.Line()
    line_chart.title = txt_id
    line_chart.x_labels = map(str, txt_content)
    line_chart.add(txt_id, txt_content)
    line_chart.render_to_file('ecs.svg')

ecs = getEcsMetric(metric,uid,key,userid,instanceid)
