#!/usr/bin/env python
#ecoding=utf8
#自动删除elasticsearch数据库保留较久的数据
#普通数据保留时间为daysToKeep，access日志保留时间为access_date
#pip install elasticsearch  安装elasticsearch包
import datetime
import re
from elasticsearch import Elasticsearch


daysToKeep = 90
es = Elasticsearch('localhost:9200',timeout=60.0)
keep_time = (datetime.datetime.now() - datetime.timedelta(days=daysToKeep)).strftime("%Y.%m.%d")

#获取indices
indices_list = []
result = es.cat.indices()
data = result.splitlines()
#过滤.kibana的indices
del_kibana = re.compile('kibana')
lines = [line for line in data if del_kibana.search(line) is None ]
#print(lines)

for i in range(len(lines)):
    indices_list.append(re.split(r' ',lines[i])[2])

print(indices_list)
#获取index，留着或许以后有用
#index_data = es.search()["hits"]["hits"]
#for i in range(len(lines)):
#    index_list.append(index_data[i]["_id"])

#一次跑太多会提示out of range，所以分每50个一批跑，下面try/except是因为indices格式有*-*-date，*-date
times = len(indices_list)/50
x = 1
while x <= times:
    index_max = 50*x
    index_min = 50*(x-1)
    for y in range(index_min,index_max):
        try:
            idx_date = re.split(r'\-',indices_list[y])[4]
        except:
            print(idx_date)
        else:
            if idx_date < keep_time:
                print "Deleting index: %s" % (indices_list[y])
                es.indices.delete(index=indices_list[y])
    x = x+1

#因为到最后x又加了1，所以下面减去1
for i in range((x-1)*50,len(indices_list)):
    try:
        idx_date = re.split(r'\-',indices_list[i])[3]
    except:
        print(idx_date)
    else:
        if idx_date < keep_time:
            print "Deleting index: %s" % (indices_list[i])
            es.indices.delete(index=indices_list[i])

#下面是system-ngxaccess,web-ngxaccess 保留7天
access_date = 7
access_keep_time = (datetime.datetime.now() - datetime.timedelta(days=access_date)).strftime("%Y.%m.%d")
save_access = re.compile('ngxaccess')
access_lines = [line for line in data if save_access.search(line) is not None ]
access_indices_list = []
for i in range(len(access_lines)):
    access_indices_list.append(re.split(r' ',access_lines[i])[2])
for z in range(len(access_indices_list)):
    access_idx_date = re.split(r'\-',access_indices_list[z])[2]
    if access_idx_date < access_keep_time:
        print "Deleting index: %s" % (access_indices_list[z])
        #es.indices.delete(index=access_indices_list[z])
