#coding=utf8
import shelve
from flask import Flask,request,render_template,redirect,escape,Markup
from datetime import datetime


application = Flask(__name__)

DATA_FILE = 'message.dat'

def save_data(name,comment,create_at):
    database = shelve.open(DATA_FILE)

    #open shelve file
    if 'greeting_list' not in database:
        greeting_list=[]
    else:
        greeting_list=database['greeting_list']

    #append the data into the list top
    greeting_list.insert(0,{
        'name':name,
        'comment':comment,
        'create_at':create_at,
    })

    #update
    database['greeting_list']=greeting_list

    #close
    database.close()

def load_data():
    database = shelve.open(DATA_FILE)
    greeting_list = database.get('greeting_list',[])
    database.close()
    return greeting_list

@application.route('/')
def index():
    greeting_list = load_data()
    return render_template('index.html',greeting_list=greeting_list)

#flask通过request.form 获取从表单提交的数据，保存数据后，通过redirect函数返回首页
@application.route('/post',methods=['POST'])
def post():
    name = request.form.get('name')
    comment = request.form.get('comments')
    create_at = datetime.now()
    save_data(name, comment, create_at)
    return redirect('/')

#添加模板过滤器，因为表单中多行评论提交后，不会正确显示
@application.template_filter('nl2br')
def nl2br_filters(s):
    return escape(s).replace('\n', Markup('</br>'))

#添加过滤器,评论时间显示到了毫秒
@application.template_filter('datetime_fmt')
def datetime_fmt_filter(dt):
    return dt.strftime('%Y/%m/%d %H:%M:%S')


if __name__=='__main__':
    application.run('127.0.0.1',8000,debug=True)
