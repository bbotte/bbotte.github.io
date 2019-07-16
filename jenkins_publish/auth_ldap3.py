from flask import request,session,Response
from ldap3 import Server, Connection, SIMPLE, SYNC, ALL
from functools import wraps
import logging_config
import logging
import json

auth_logger = logging.getLogger('verbose')

def ldap_authenticate(request,username,password,groups_allowed=True):
  #change these values to what is appropriate for your environment
  id_name="uid"
  ldap_host="192.168.0.2"
  ldap_port="389"
  bind_dn="cn=Manager,dc=bbotte,dc=com"
  bind_pass="123456"
  user_base="ou=People,dc=bbotte,dc=com"
  
  #bind with service account
  s = Server(ldap_host, port=int(ldap_port), get_info=ALL)
  c = Connection(
    s,
    authentication=SIMPLE, 
    user=bind_dn,
    password=bind_pass,
    check_names=True, 
    lazy=False, 
    client_strategy=SYNC, 
    raise_exceptions=False)
  c.open()
  c.bind()
  if c.bound:
    #once bound, check username provided and get cn, memberOf list and mail
    # get cn_name
    c.search(user_base,'(%s=%s)'%(id_name,username),attributes=['cn','mail'])
    c.unbind
    try: 
      cn_name=c.entries[0].cn
    except:
      print("user cn cannot be found")
      auth_logger.error("user cn cannot be found")
      
    session['username']=username
    return True
  else:
    auth_logger.debug('ldap bind failed')
    c.unbind()
    return False

def auth_401():
    return Response('You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Input ldap USER and PASSWORD"'})

def ldap_protected(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    # this can be configured and taken from elsewhere
    # path, method, groups_allowed (users in Allowed Users group will be allowed to access / with a GET method)
    authorization_config = {
      "/": {
         "GET": ["Allowed Users"]
      }
    }

    auth_endpoint_rule = authorization_config.get(request.url_rule.rule)
    if auth_endpoint_rule is not None:
      groups_allowed = auth_endpoint_rule.get(request.method) or True
    else:
      groups_allowed = True
    
    auth = request.authorization
    if not ('username' in session):
      if not auth or not ldap_authenticate(request,auth.username, auth.password, groups_allowed):
        return auth_401()
    else:
      auth_logger.debug("%s calling %s endpoint"%(session['username'],f.__name__))
    return f(*args, **kwargs)
  return decorated

