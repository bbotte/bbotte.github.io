#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask,render_template,request
from subprocess import Popen,PIPE
from config import NAME
from config import HOST
from config import PORT
import json

app = Flask(__name__)

def redis_get(rediskey):
    redis_statement="""for i in {{0..15}};do redis-cli -h {host} -p {port} -n ${{i}} keys '{rediskey}'|sed '/^$/d';done|while read j;do echo -e "\\"$j\\":"; for k in {{0..15}};do redis-cli -h {host} -p {port} -n ${{k}} get $j |sed '/^$/d'|awk '{{printf "\\"%s\\"",$1}}';done ;echo ',';done""".format(rediskey=rediskey,host=HOST, port=PORT)
    p = Popen(redis_statement, stdout=PIPE, shell=True)
    stdout, stderr = p.communicate()
    r = stdout.decode()
    r="".join(r.replace('\n',''))
    r=r.rstrip(",")
    r="{"+r+"}"
    return r

@app.route('/',methods=['POST','GET'])
def index():
    rediskey = request.form.get('rediskey')
    redis_result=redis_get(rediskey)
    return render_template('index.html',redis_result=redis_result)

if __name__ == '__main__':
    app.run('0.0.0.0','8000',debug=True)

