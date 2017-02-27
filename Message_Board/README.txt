Message_Board

需要安装的模块
flask

也可以用下面方式导入评论数据:
# ipython
In [2]: import datetime
In [3]: from message_board import save_data
In [4]: save_data('test','test_comment',datetime.datetime(2017,02,27,11,0,0))
In [5]: from message_board import load_data
In [6]: load_data()
Out[6]:
[{'comment': 'test_comment',
  'create_at': datetime.datetime(2017, 2, 27, 11, 0),
    'name': 'test'}]


服务启动:
python message_board.py

