#!/usr/bin/env python

import sys
sys.path.append("../")

from harborclient import harborclient

host = "harbor.bbotte.com"
user = "admin"
password = "Harbor345"
port = 5000

client = harborclient.HarborClient(host, port, user, password)

# Create user
username = "test-username"
email = "test-email@gmail.com"
password = "test-password"
realname = "test-realname"
comment = "test-comment"
client.create_user(username, email, password, realname, comment)
