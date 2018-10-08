#!/usr/bin/env python

import sys
sys.path.append("../")

from harborclient import harborclient

host = "harbor.bbotte.com"
user = "admin"
password = "Harbor345"
port = 5000

client = harborclient.HarborClient(host,port, user, password)

# Delete repository
repo_name = "library/cirros"
client.delete_repository(repo_name)
