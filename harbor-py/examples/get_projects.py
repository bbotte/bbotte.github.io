#!/usr/bin/env python

import sys
sys.path.append("../")

from harborclient import harborclient

host = "harbor.bbotte.com"
user = "admin"
password = "Harbor345"
port = 5000

client = harborclient.HarborClient(host,port, user, password)

# Get all projects
all_projects = client.get_projects()
for i in all_projects:
    print(i['name'])
