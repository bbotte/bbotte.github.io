---
layout: default
---

# python写一个简单的留言板

用python练个手，写个最简单的留言板，用flask框架，shelve存储

```
vim message_board.py
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
```

主页index.html

```
<!DOCTYPE html>
<html>
<head lang="en">
    <meta charset="UTF-8">
    <title>Message Board</title>
    <link rel="stylesheet" href="../static/main.css" type="text/css">
</head>
<!--将css记录的id和class设置在html指定位置-->
<body>
    <div id="main">
        <h1>Message Board</h1>
        <div id="form-area">
            <p>please comment here:</p>
            <form action="/post" method="POST">
                <table>
                    <tr>
                        <th>Name</th>
                        <td>
                            <input type="text" size="20" name="name" />
                        </td>
                    </tr>
                    <tr>
                        <th>Comment</th>
                        <td>
                            <textarea rows="5" cols="40" name="comments"> </textarea>
                        </td>
                    </tr>
                </table>
                <p><button type="submit">Commit</button></p>
            </form>
        </div>
        <div id="entries-area">
            <h2>the comments history</h2>
            <div class="entry">
                {% for greeting in greeting_list %}
                    <h3>{{ greeting.name }} commented at {{ greeting.create_at|datetime_fmt }}</h3>
                    <p>{{ greeting.comment|nl2br }}</p>
                {% endfor %}
                </p>
            </div>
        </div>
    </div>
</body>
</html>
```

css样式

```
body {
    margin:0;
    padding: 0;
    color: #000E41;
    background-color: #004080;
}
 
h1 {
    padding: 0 1em;
    color: #FFFFFF;
}
 
#main {
    padding: 0;
}
 
#form-area {
    padding: 0.5em 2em;
    background-color: #78B8F8;
}
 
#entries-area {
    padding: 0.5em 2em;
    background-color: #FFFFFF;
}
 
.entry p{
    padding: 0.5em 1em;
    background-color: #DBDBFF;
}
```

文件结构如下：

```
tree .
.
├── README.txt
├── message.dat.db
├── message_board.py
├── message_board.pyc
├── static
│   └── main.css
└── templates
    └── index.html
```

或者查看github <https://github.com/bbotte/bbotte.com/tree/master/Message_Board>

```
需要安装的模块
pip install flask
 
提交评论:
在web页面即可提交
也可以用下面方式导入评论数据:
 
# ipython
In [1]: import datetime
In [2]: from message_board import save_data
In [3]: save_data('test','test_comment',datetime.datetime(2017,02,27,11,0,0))
In [4]: from message_board import load_data
In [5]: load_data()
Out[5]:
[{'comment': 'test_comment',
  'create_at': datetime.datetime(2017, 2, 27, 11, 0),
    'name': 'test'}]
 
服务启动:
python message_board.py
```

![simple message board](../images/2017/02/simple_message_board.png)

2017年02月27日 于 [linux工匠](http://www.bbotte.com/) 发表

