#!/usr/bin/env python

import sys
sys.path.append("../")

from harborclient import harborclient

host = "harbor.bbotte.com"
user = "admin"
password = "Harbor345"
port = 5000

client = harborclient.HarborClient(host, port, user, password)

# Get project id from name
project_name = "k8s"
print(client.get_project_id_from_name(project_name))
