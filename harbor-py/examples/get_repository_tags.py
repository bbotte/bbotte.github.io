#!/usr/bin/env python

import sys
sys.path.append("../")

from harborclient import harborclient

host = "harbor.bbotte.com"
user = "admin"
password = "Harbor345"
port = 5000

client = harborclient.HarborClient(host, port, user, password)

# Get repository tags
repo_name = "base/centos"
print(client.get_repository_tags(repo_name))
