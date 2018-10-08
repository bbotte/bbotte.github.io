#!/usr/bin/env python

import sys
sys.path.append("../")

from harborclient import harborclient

host = "harbor.bbotte.com"
user = "admin"
password = "Harbor345"
port = 5000

client = harborclient.HarborClient(host,port ,user, password)

# Get all repositories
project_id = 5
print(client.get_repositories(project_id))
