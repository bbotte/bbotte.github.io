#!/usr/bin/env python

import sys
sys.path.append("../")

from harborclient import harborclient

host = "harbor.bbotte.com"
user = "admin"
password = "Harbor345"
port = 5000

client = harborclient.HarborClient(host, port, user, password)

# Get repository manifests
repo_name = "devops/redis"
tag = "v0.1"
print(client.get_repository_manifests(repo_name, tag))
