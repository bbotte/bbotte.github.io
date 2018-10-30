#!/usr/bin/python
# ########################################
# Function:    CMS self-defined monitor SDK
# Usage:       python cms_post.py ali_uid, metric_name, value, fields
# Author:      CMS Dev Team
# Company:     Aliyun Inc.
# Version:     1.0
# Description: Since Python 2.6, please check the version of your python interpreter
# ########################################
import sys
import time
import socket
import random
import urllib
import httplib
import json
import logging
from logging.handlers import RotatingFileHandler

REMOTE_HOST = 'open.cms.aliyun.com'
REMOTE_PORT = 80
REMOTE_MONITOR_URI = "/metrics/put"


def post(ali_uid, metric_name, metric_value, unit, fields):
    # init logger
    logger = logging.getLogger('post')
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(filename="/tmp/post.log", mode='a', maxBytes=1024 * 1024, backupCount=3)
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    socket.setdefaulttimeout(10)

    # convert dimensions
    kv_array = fields.split(',')
    dimensions = {}
    for kv in kv_array:
        kv_array = kv.split('=')
        #print "dimensions:%s=%s" %(kv_array[0],kv_array[1])
        dimensions[kv_array[0]] = kv_array[1]
    json_str = json.dumps(dimensions)

    #current timestamp
    timestamp = int(time.time() * 1000)

    #concate to metrics
    metrics = '[{"metricName": "%s","timestamp": %s,"value": %s, "unit": "%s", "dimensions": %s}]' % (
        metric_name,str(timestamp),str(metric_value),unit, json_str)

    params = {"userId": ali_uid, "namespace": "acs/custom/%s" % ali_uid, "metrics": metrics}
    print params
    #report at random 5 seconds
    interval = random.randint(0, 5000)
    time.sleep(interval / 1000.0)

    data = urllib.urlencode(params)
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Connection": "close"}
    exception = None
    http_client = None
    try:
        http_client = httplib.HTTPConnection(REMOTE_HOST, REMOTE_PORT)
        try:
            http_client.request(method="POST", url=REMOTE_MONITOR_URI, body=data, headers=headers)
            response = http_client.getresponse()
            if response.status == 200:
		print "upload metric succeed!"
                return
            else:
                print "response code %d, content %s " % (response.status, response.read())
                logger.warn("response code %d, content %s " % (response.status, response.read()))
        except Exception, e:
            exception = e
    finally:
        if http_client:
            http_client.close()
        if exception:
            logger.error(exception)


if __name__ == '__main__':
    #print len(sys.argv)
    #for arg in sys.argv:
    #    print arg
    if len(sys.argv) != 6:
        print "argv format should be:  aliuid, metricName, metricValue, unit, kvpairs"
 	print """
        for example:
	python cms_post.py 1736511134389110 'Perm_Generation' 10 'Percent' 'instanceId=cmssiteprobeqd115029112222'
	"""
        exit(1)
    post(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
