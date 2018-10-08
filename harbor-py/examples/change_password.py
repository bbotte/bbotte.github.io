#!/usr/bin/env python

import sys
sys.path.append("../")

from harborclient import harborclient

host = "harbor.bbotte.com"
user = "admin"
password = "Harbor345"
port = 5000

client = harborclient.HarborClient(host, port, user, password)

# Change password
user_id = 2
old_password = "test-password"
new_password = "new-password"
client.change_password(user_id, old_password, new_password)
