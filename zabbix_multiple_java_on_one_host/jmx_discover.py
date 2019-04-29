#!/usr/bin/env python
# cat jmx_service_port
# system 9999
import json
l = list()
with open('/etc/zabbix/zabbix_agentd.d/jmx_service_port') as f:
    lines = f.readlines()
for i in lines:
    S = i.strip('\n').split()[0]
    P = i.strip('\n').split()[1]
    d = {}
    d['{#JAVA_NAME}'] = S
    d['{#JMX_PORT}'] = P
    l.append(d)
data = {}
data['data'] = l
print(json.dumps(data,sort_keys=True, indent=4))
