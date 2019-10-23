# pyenv virtualenv构建独立的python环境

不管是线上还是开发环境都需要根据python版本设置独立的环境，避免与系统环境交叉而出错，pyenv和插件virtualenv刚好建立隔离的python环境，ipython又方便https://pypi.python.org/pypi 安装包的自动安装

1，环境准备，安装设置pyenv

```
# cat /etc/centos-release
CentOS release 6.7 (Final)
 
# yum install git python-pip
# yum install openssl-devel readline-devel sqlite-devel bzip2-devel
# git clone git://github.com/yyuu/pyenv.git ~/.pyenv
# less ~/.pyenv/README.md #使用文档
 
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
exec $SHELL
 
# pyenv
pyenv 1.0.6-8-g2d5fc1b
Usage: pyenv <command> [<args>]
 
Some useful pyenv commands are:
commands List all available pyenv commands
local Set or show the local application-specific Python version
global Set or show the global Python version
shell Set or show the shell-specific Python version
install Install a Python version using python-build
uninstall Uninstall a specific Python version
rehash Rehash pyenv shims (run this after installing executables)
version Show the current Python version and its origin
versions List all Python versions available to pyenv
which Display the full path to an executable
whence List all Python versions that contain the given executable
```

2，安装需要的python版本，设置虚拟环境

```
# pyenv install -l
# pyenv install 2.7.12
# pyenv versions
* system (set by /root/.pyenv/version)
2.7.12
```

pyenv virtualenv 是 pyenv 的插件,activate 和 deactivate 用于激活/禁用已有虚拟环境

```
# git clone https://github.com/pyenv/pyenv-virtualenv ~/.pyenv/plugins/pyenv-virtualenv
 
# pyenv virtualenv -h
Usage: pyenv virtualenv [-f|--force] [VIRTUALENV_OPTIONS] [version] <virtualenv-name>
pyenv virtualenv --version
pyenv virtualenv --help
 
-f/--force Install even if the version appears to be installed already
 
# pyenv virtualenv 2.7.12 myenv
New python executable in /root/.pyenv/versions/2.7.12/envs/myenv/bin/python2.7
Also creating executable in /root/.pyenv/versions/2.7.12/envs/myenv/bin/python
Installing setuptools, pip, wheel...done.
Ignoring indexes: https://pypi.python.org/simple
Requirement already satisfied (use --upgrade to upgrade): setuptools in /root/.pyenv/versions/2.7.12/envs/myenv/lib/python2.7/site-packages
Requirement already satisfied (use --upgrade to upgrade): pip in /root/.pyenv/versions/2.7.12/envs/myenv/lib/python2.7/site-packages
# pyenv versions
* system (set by /root/.pyenv/version)
2.7.12
2.7.12/envs/myenv
myenv
```

3，设置python环境的目录

```
# exec $SHELL
# pyenv activate myenv
pyenv-virtualenv: prompt changing will be removed from future release. configure `export PYENV_VIRTUALENV_DISABLE_PROMPT=1' to simulate the behavior.
(myenv) [root@localhost ~]# pyenv deactivate myenv
```

我们需要设置一个文件夹，在文件夹内都用到虚拟的python环境，即上面创建的myenv，进入此文件夹自动进入pyenv环境

```
# mkdir /data
# echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
# exec $SHELL
# echo 2.7.12/envs/myenv > /data/.python-version
# cd /data/
(2.7.12/envs/myenv) [root@localhost data]#     #自动进入env环境
(2.7.12/envs/myenv) [root@localhost data]# pip install ipython
(2.7.12/envs/myenv) [root@localhost data]# ipython
/root/.pyenv/versions/2.7.12/envs/myenv/lib/python2.7/site-packages/IPython/core/history.py:228: UserWarning: IPython History requires SQLite, your history will not be saved
warn("IPython History requires SQLite, your history will not be saved")
Python 2.7.12 (default, Jan 6 2017, 16:24:02)
Type "copyright", "credits" or "license" for more information.
 
IPython 5.1.0 -- An enhanced Interactive Python.
? -> Introduction and overview of IPython's features.
%quickref -> Quick reference.
help -> Python's own help system.
object? -> Details about 'object', use 'object??' for extra details.
 
In [1]:
 
不过这样有个缺点，比如进入/var 、 /opt 等目录下，也会是pyenv的环境，那么复制系统的python-version到目录下即可
# cat ~/.python-version
system
# cp ~/.python-version /var/
# cp ~/.python-version /opt
# cd /opt/
[root@vm01 opt]#
```

还需要什么包就用pip安装吧

2017年01月06日 于 [linux工匠](http://www.bbotte.com/) 发表

































