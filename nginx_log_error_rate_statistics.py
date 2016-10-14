#!/usr/bin/env python
#ecoding=utf8
#python 3以上版本,python3以下版本更改yield from f为下面2行的注释
#curl -i -XPOST http://localhost:8086/query --data-urlencode "q=CREATE DATABASE mydb"
import os
import re
import datetime
import threading
import requests
import sys

'''nginx默认的日志格式
log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                  '$status $body_bytes_sent "$http_referer" '
                  '"$http_user_agent" "$http_x_forwarded_for"';
'''

o = re.compile(r'(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) .* .* \[(?P<time>.*)\] "(?P<method>\w+) (?P<url>[^\s]*) (?P<version>[\w|/\.\d]*)" (?P<status>\d{3}) (?P<length>\d+) "(?P<referer>[^\s]*)" "(?P<ua>.*)"')

def read_log(path):
    offset = 0
    event = threading.Event()
    while not event.is_set():
        with open(path) as f:
            if offset > os.stat(path).st_size:
                offset = 0
            f.seek(offset)
            yield from f
            #for i in f:
            #    yield i
            offset = f.tell()
        event.wait(2)


def parse(path):
    for line in read_log(path):
        m = o.search(line.rstrip('\n'))
        if m:
            data = m.groupdict()
            yield data


def aggregate(path, interval=10):
    count = 0
    traffic = 0
    error = 0
    start = datetime.datetime.now()
    for item in parse(path):
        count += 1
        traffic += int(item['length'])
        if int(item['status']) >= 300:
            error += 1
        current = datetime.datetime.now()
        print((current - start).total_seconds())
        if (current - start).total_seconds() >= interval:
             error_rate = error / count
             send(count, traffic, error_rate)
             start = current
             count = 0
             traffic = 0
             error = 0
     

def send(count, traffic, error_rate):
    line = 'access_log count={},traffic={},error_rate={}'.format(count, traffic, error_rate)
    print(line)
    res = requests.post('http://127.0.0.1:8086/write', data=line, params={'db': 'mydb'})
    if res.status_code >= 300:
        print(res.content)

if __name__ == '__main__':
    aggregate(sys.argv[1])

