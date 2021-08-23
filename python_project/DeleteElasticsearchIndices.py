#!/usr/bin/env python
#ecoding=utf8
#自动删除elasticsearch数据库保留较久的数据
#普通数据保留时间为daysToKeep
#pip install elasticsearch  安装elasticsearch包
import datetime
import re
from elasticsearch import Elasticsearch

daysToKeep = 12
es = Elasticsearch('localhost:9200',timeout=60.0)
keep_time = (datetime.datetime.now() - datetime.timedelta(days=daysToKeep)).strftime("%Y.%m.%d")

#获取indices
indices_list = []
result = es.cat.indices()
data = result.splitlines()

test_kibana = re.compile(r'test1')  #筛选包含test1的index
test2_kibana = re.compile(r'test2')   #筛选包含test2的index
lines = [line for line in data if test1_kibana.search(line) is not None or test2_kibana.search(line) is not None ]

for i in range(len(lines)):
    indices_list.append(re.split(r' ',lines[i])[2])

for y in range(len(indices_list)):
    idx_date = re.split(r'\-',indices_list[y])[-1]
    if idx_date < keep_time:
        print "Deleting index: %s" % (indices_list[y])
        es.indices.delete(index=indices_list[y])
