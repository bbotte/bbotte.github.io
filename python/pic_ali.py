#!/usr/bin/env python
#ecoding=utf8
import datetime
import json
import pygal
from aliyunsdkcore import client
from aliyunsdkcms.request.v20151020 import QueryMetricRequest

uid="XXXXXX"
key="XXXXXXXXXXX"
userid="XXXXX"

class getMetric(object):
    def __init__(self,project,metric,instanceid):
	self.project = project
	self.metric = metric
	self.instanceid = instanceid
	
    def timest():
        clt = client.AcsClient(uid,key,'cn-qingdao')
        startTime=datetime.datetime.now() - datetime.timedelta(hours=167)
        startTimeStr=startTime.strftime("%Y-%m-%d %H:%M:%S")
        print startTimeStr

    def getEcsMetric(clt,startTimeStr,project,metric,instanceid):
        request = QueryMetricRequest.QueryMetricRequest()
        request.set_accept_format('json')
        request.set_Project(self.project)
        request.set_Metric(self.metric)
        request.set_StartTime(startTimeStr)
        request.set_Dimensions("{userId:userid, instanceId:self.instanceid}")
        result = clt.do_action(request)
        return result

    def getvalue(self):
        #getresult = getMetric(project,metric,instanceid)
        data_json = json.loads(result)
        data = data_json["Datapoints"]["Datapoint"]
        txt_t = []
        txt_a = []
        for i in range(len(data)):
            dt  = (str(data[i]["timestamp"]))[:10]
            txt_time = datetime.datetime.fromtimestamp(int(dt)).strftime('%Y-%m-%d %H:%M:%S')
            txt_t.append(txt_time)
            txt_a.append(data[i]["Average"])
            txt_id = data[i]["instanceId"]

    def pic(self):
        line_chart = pygal.Line()
        line_chart.title = txt_id
        line_chart.x_labels = map(str, txt_t)
        line_chart.add(txt_id, txt_a)
        line_chart.render_to_file('bar_chart.svg')
    
def main(project="acs_ecs",metric="CPUUtilization",instanceid="XXX"):
    getresult = getMetric(project,metric,instanceid)

if __name__ == "__main__":
    main()
