#!/usr/bin/env python

import sys
sys.path.append("../")

from harborclient import harborclient

host = "harbor.bbotte.com"
user = "admin"
password = "Harbor345"
port = 5000

client = harborclient.HarborClient(host, port, user, password)

# Update user profile
user_id = 2
email = "new@gmail.com"
realname = "new_realname"
comment = "new_comment"
client.update_user_profile(user_id, email, realname, comment)
