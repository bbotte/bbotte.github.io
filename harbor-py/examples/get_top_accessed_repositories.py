#!/usr/bin/env python

import sys
sys.path.append("../")

from harborclient import harborclient

host = "harbor.bbotte.com"
user = "admin"
password = "Harbor345"
port = 5000

client = harborclient.HarborClient(host, port, user, password)

# Get top accessed respositories
print(client.get_top_accessed_repositories())

# Get top accessed respositories with count
count = 1
print(client.get_top_accessed_repositories(count))
