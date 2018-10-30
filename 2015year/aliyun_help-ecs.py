#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys,os
import urllib, urllib2
import base64
import hmac
import hashlib
from hashlib import sha1
import time
import uuid
import json
from optparse import OptionParser
import ConfigParser

access_key_id = '';
access_key_secret = '';
ecs_server_address = 'https://ecs.aliyuncs.com'
CONFIGFILE = os.path.expanduser('~') + '/.aliyuncredentials'
CONFIGSECTION = 'Credentials'
cmdlist = '''
Instance
    CreateInstance regionid imageid instancetype securitygroupid instancename internetmaxbandwidthout password 
                   SystemDisk.Category DataDisk.n.Category DataDisk.n.Size DataDisk.n.Snapshot InternetChargeType
    StopInstance
    RebootInstance
    ResetInstance
    ModifyInstanceSpec
    ModifyInstanceAttribute
    DescribeInstanceStatus
    DescribeInstanceAttribute
    DeleteInstance

Disk
    AddDisk
    DeleteDisk
    DescribeInstanceDisks
    ReplaceSystemDisk
    ResetDisk
    ReInitDisk

Snapshot
    CreateSnapshot
    DeleteSnapshot
    DescribeSnapshots
    DescribeSnapshotAttribute
    

Images
    DescribeImages
    CreateImage
    DeleteImage

IP
    AllocatePublicIpAddress
    ReleasePublicIpAddress

SecurityGroup
    CreateSecurityGroup
    AuthorizeSecurityGroup
    DescribeSecurityGroupAttribute
    DescribeSecurityGroups
    RevokeSecurityGroup
    DeleteSecurityGroup
    JoinSecurityGroup
    LeaveSecurityGroup

Common
    DescribeRegions
    GetMonitorData
    DescribeInstanceTypes
'''

def percent_encode(str):
    res = urllib.quote(str.decode(sys.stdin.encoding).encode('utf8'), '')
    res = res.replace('+', '%20')
    res = res.replace('*', '%2A')
    res = res.replace('%7E', '~')
    return res

def compute_signature(parameters, access_key_secret):
    sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])

    canonicalizedQueryString = ''
    for (k,v) in sortedParameters:
        canonicalizedQueryString += '&' + percent_encode(k) + '=' + percent_encode(v)

    stringToSign = 'GET&%2F&' + percent_encode(canonicalizedQueryString[1:])

    h = hmac.new(access_key_secret + "&", stringToSign, sha1)
    signature = base64.encodestring(h.digest()).strip()
    return signature

def compose_url(user_params):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    parameters = { \
            'Format'        : 'JSON', \
            'Version'       : '2014-05-26', \
            'AccessKeyId'   : access_key_id, \
            'SignatureVersion'  : '1.0', \
            'SignatureMethod'   : 'HMAC-SHA1', \
            'SignatureNonce'    : str(uuid.uuid1()), \
            'TimeStamp'         : timestamp, \
    }

    for key in user_params.keys():
        parameters[key] = user_params[key]

    signature = compute_signature(parameters, access_key_secret)
    parameters['Signature'] = signature
    url = ecs_server_address + "/?" + urllib.urlencode(parameters)
    return url

def make_request(user_params, quiet=False):
    url = compose_url(user_params)
    request = urllib2.Request(url)

    try:
        conn = urllib2.urlopen(request)
        response = conn.read()
    except urllib2.HTTPError, e:
        print(e.read().strip())
        raise SystemExit(e)

    #make json output pretty, this code is copied from json.tool
    try:
        obj = json.loads(response)
        if quiet:
            return obj
    except ValueError, e:
        raise SystemExit(e)
    json.dump(obj, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write('\n')

def configure_accesskeypair(args, options):
    if options.accesskeyid is None or options.accesskeysecret is None:
        print("config miss parameters, use --id=[accesskeyid] --secret=[accesskeysecret]")
        sys.exit(1)
    config = ConfigParser.RawConfigParser()
    config.add_section(CONFIGSECTION)
    config.set(CONFIGSECTION, 'accesskeyid', options.accesskeyid)
    config.set(CONFIGSECTION, 'accesskeysecret', options.accesskeysecret)
    cfgfile = open(CONFIGFILE, 'w+')
    config.write(cfgfile)
    cfgfile.close()

def setup_credentials():
    config = ConfigParser.ConfigParser()
    try:
        config.read(CONFIGFILE)
        global access_key_id
        global access_key_secret
        access_key_id = config.get(CONFIGSECTION, 'accesskeyid')
        access_key_secret = config.get(CONFIGSECTION, 'accesskeysecret')
    except Exception, e:
        print("can't get access key pair, use config --id=[accesskeyid] --secret=[accesskeysecret] to setup")
        sys.exit(1)

def describe_instances(regionid):
    user_params = {}
    user_params['Action'] = 'DescribeZones'
    user_params['RegionId'] = regionid
    obj = make_request(user_params, quiet=True)

    zones = []
    print('%21s %21s %10s %15s' % ('InstanceId', 'InstanceName', 'Status', 'InstanceType'))
    for zone in obj['Zones']['Zone']:
        user_params = {}
        user_params['Action'] = 'DescribeInstanceStatus'
        user_params['RegionId'] = regionid
        user_params['ZoneId'] = zone['ZoneId']
        instances = make_request(user_params, quiet=True)
        if len(instances) > 0:
            for i in instances['InstanceStatuses']['InstanceStatus']:
                instanceid = i['InstanceId']
                params = {}
                params['Action'] = 'DescribeInstanceAttribute' 
                params['InstanceId'] = instanceid
                res = make_request(params, quiet=True)
                print('%21s %21s %10s %15s' % (res['InstanceId'], res['InstanceName'], res['Status'], res['InstanceType']))

if __name__ == '__main__':
    parser = OptionParser("%s Action Param1=Value1 Param2=Value2\n  DescribeImages RegionId=cn-qingdao ImageOwnerAlias=self" % sys.argv[0])
    parser.add_option("-i", "--id", dest="accesskeyid", help="specify access key id")
    parser.add_option("-s", "--secret", dest="accesskeysecret", help="specify access key secret")

    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        sys.exit(0)

    if args[0] == 'help':
        print cmdlist
        sys.exit(0)
    if args[0] != 'config':
        setup_credentials()
    else: #it's a configure id/secret command
        configure_accesskeypair(args, options)
        sys.exit(0)

    user_params = {}
    idx = 1
    if not sys.argv[1].lower().startswith('action='):
        user_params['action'] = sys.argv[1]
        idx = 2

    for arg in sys.argv[idx:]:
        try:
            key, value = arg.split('=')
            user_params[key.lower()] = value
        except ValueError, e:
            print(e.read().strip())
            raise SystemExit(e)

    if user_params['action'] == 'ls':
      describe_instances(user_params['regionid'])
    else:
      make_request(user_params)

