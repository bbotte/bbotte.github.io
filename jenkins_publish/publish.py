#!/usr/bin/env python
# -*- coding: utf-8 -*-
#针对一个jenkins项目发布多个环境，比如web项目，有dev、uat环境的jenkins多线程脚本
from flask import Flask,render_template,request,Response,session
import json
import os
import logging
import auth_ldap3
import jenkins
import time
from threading import Thread

#以下2个参数均为jenkins job中项目所需参数
resource_list = ['test1',]
emailtest_list = ['something',]

thread_list = list()
service_images_list = list()
app_logger = logging.getLogger('verbose')
app = Flask(__name__)
app.debug=True


class MyThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.service_build_list= list()

    def start(self,service_build_list):
        local_threads = []
        for i in range(len(service_build_list)):
            servicename = service_build_list[i]["service_name"]
            serviceparams = service_build_list[i]["service_params"]
            t = Thread(target=jenkins_worker,args=(servicename,serviceparams))
            t.setDaemon(True)
            thread_list.append(t)
            local_threads.append(t)
        for t in local_threads:
            t.start()
        for t in thread_list:
            t.join()

def jenkins_worker(servicename,serviceparams):
    #pip uninstall jenkins && pip install python-jenkins==1.4.0
    jenkins_server = jenkins.Jenkins('http://jenkins.bbotte.com',username='devops', password='123456')
    j_result = ''
    j_run = ''
    service_V = ''
    last_build_number = jenkins_server.get_job_info(servicename)['nextBuildNumber']-1
    lastResult = jenkins_server.get_build_info(servicename,last_build_number)['result']
    if lastResult == "SUCCESS":
        lastCommitID = jenkins_server.get_build_env_vars(servicename,last_build_number)['envMap']['GIT_COMMIT'][0:7]
        try:
            lastplatform = jenkins_server.get_build_env_vars(servicename,last_build_number)['envMap']['platform']
        except:
            lastplatform = ''
    else:
        lastCommitID = ''
        lastplatform = ''
    currentNumber = last_build_number+1
    currentCommitID = serviceparams['branch']
    if 'platform' in serviceparams:
        platform = serviceparams['platform']
    else:
        platform = ''
    if (currentCommitID == lastCommitID) and (platform != 'uat') and (lastplatform !='uat'):
        service_V = jenkins_server.get_build_env_vars(servicename,last_build_number)['envMap']['Version']
        print(servicename,service_V)
        service_images_list.append(servicename+':'+ service_V)
    else:
        jenkins_server.build_job(servicename, serviceparams)
        while True:
            time.sleep(5)
            try:
                j_result= jenkins_server.get_build_info(servicename,currentNumber)['result']
            except:
                j_result = ''
            j_running = jenkins_server.get_running_builds()
            j_run = ""
            j_queue = jenkins_server.get_queue_info()
            for q in range(len(j_running)):
                if j_running[q]['name'].lower() == servicename:
                    j_run = servicename
            if (j_result == "SUCCESS" and j_run != servicename) or j_result == "FAILURE":
                break
            else:
                if j_queue:
                    for p in j_queue:
                        if p['task']['name'].lower() == servicename:
                            continue
        try:
            service_V = jenkins_server.get_build_env_vars(servicename,currentNumber)['envMap']['Version']
        except:
            service_V = "ERROR"
        service_images_list.append(servicename+':'+ service_V)
    return service_images_list


@app.route('/',methods=['POST','GET'])
@auth_ldap3.ldap_protected #this makes this endpoint protected
def root():
    message = "logged in as %s"% session["username"]
    app_logger.debug("%s"%message)
    jenkinsplatform = request.form.get('select')
    if jenkinsplatform:
        with open("/tmp/jenkinsplatform",'w') as f:
            f.write(jenkinsplatform)
    return render_template('index.html',data=[
	     #同一个jenkins Job，多个环境，以参数的方式传递给jenkins，
		 #host是在页面中显示便于理解的环境名称
        {'name':'dev','host':"dev环境"},
		{'name':'uat','host':"uat环境"},
                                 ],
        )

@app.route("/logout")
def logout():
  try:
      app_logger.debug("logging out %s"%session["username"])
      session.pop('username', None)
      message = "logged out"
  except:
      message = "not logged in"
  return Response(json.dumps("%s"%message), mimetype="application/json")


@app.route("/buildimages", methods=['GET','POST'])
def buildimages():
    global service_images_list
    service_images_list = list()
    service_build_list = list()
    service_name = str()
    buildImages = str()
    with open('/tmp/jenkinsplatform') as f:
        l = f.readline().split()
        platform = l[0]
    print(platform)
    if request.method == 'POST':
        service_info = request.form.getlist('buildImages')
        service_info = service_info[0].splitlines()
        for i in range(len(service_info)):
            if service_info[i] != '':
                service_ver = dict()
                service_params = dict()
                service_name = service_info[i].split()[0].lower()
                service_ver['service_name'] = service_name
                if len(service_info[i].split()[1]) > 6:
                    service_params['branch'] = service_info[i].split()[1][:7]
                else:
                    service_params['branch'] = service_info[i].split()[1]
                if platform == "uat":
                    if service_info[i].split()[0] in emailtest_list:
                        service_params['platform'] = 'uat'
                if service_name == "frontend":
                    if platform in resource_list:
                        service_params['resources'] = platform
                    else:
                        service_params['resources'] = 'default'
                service_ver['service_params']=service_params
                service_build_list.append(service_ver)
        print(service_build_list)
        mythread.start(service_build_list=service_build_list)
        for i in service_images_list:
            S = i.split(':')[0]
            V = i.split(':')[1]
            buildImages += S+':'+V+'\n'
        print("jenkins构建完成")
    return render_template('buildimages.html',buildImages = buildImages)


mythread = MyThread()
def run():
    app.secret_key = os.urandom(24)
    app_logger.debug("application started")
    app.run()

if __name__=="__main__":
    app.secret_key = os.urandom(24)
    app_logger.debug("application started")
    app.run('0.0.0.0','8000')
