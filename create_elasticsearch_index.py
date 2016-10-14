#!/usr/bin/env python
#ecoding=utf8
#提前一天创建es的index
#pip install elasticsearch
import datetime
import re
from elasticsearch import Elasticsearch
import time
 
es = Elasticsearch('127.0.0.1:9200',timeout=5.0)
#获取indices
result = es.cat.indices()
data = result.splitlines()
 
d = datetime.datetime.now().strftime("%Y.%m.%d")
l = [i for i in data if re.compile(d).search(i) is not None ]
 
#index格式为 *-*-date
tomorrow = str(datetime.date.today() + datetime.timedelta(days=1)).replace('-','.')
year = str(datetime.date.today().year)
for i in range(len(l)):
    esIndex = re.split(year,list(re.split(r' ',l[i]))[2])[0] + tomorrow
    print "create es index %s" % (esIndex)
    time.sleep(23)
    es.indices.create(index=esIndex)
