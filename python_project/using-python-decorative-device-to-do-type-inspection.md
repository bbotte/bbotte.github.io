---
layout: default
---

# 利用python装饰器做类型检查

python的装饰器使用方式有多种，在[小议python的迭代iterative和递归recursive](http://bbotte.com/python-dev/python-iterative-and-recursive/)中使用装饰器得出python脚本的执行时间，下面说一下对输入类型做检查

```
def require(arg_name, allowed_type):
    """ Checks that arg_name is an instance of allowed type. 
        If not, attempts to convert the respective argument to the allowed type """
 
    def make_wrapper(f):
        if hasattr(f, "wrapped_args"):
            wrapped_args = getattr(f, "wrapped_args")
        else:
            code = f.func_code
            wrapped_args = list(code.co_varnames[:code.co_argcount])
 
        try:
            arg_index = wrapped_args.index(arg_name)
        except ValueError:
            raise NameError, arg_name
 
        def wrapper(*args, **kwargs):
            args=list(args)
 
            if len(args) > arg_index:
                arg = args[arg_index]
                if not isinstance(arg, allowed_type):
                    args[arg_index]=allowed_type(args[arg_index])
            else:
                if arg_name in kwargs:
                    arg = kwargs[arg_name]
                    if not isinstance(arg, allowed_type):
                        kwargs[arg_name]=allowed_type(kwargs[arg_name])
 
            return f(*args, **kwargs)
 
        wrapper.wrapped_args = wrapped_args
        return wrapper
 
    return make_wrapper
```

```
@require('x',str)
@require('y',int)
def foo(x,y):
    return x*y
```

也可以对其他类型做装饰

因为在python里面，

1，函数可以返回另一个函数

2，函数可以当做参数传递

3，要使用装饰器的话，需要提前定义装饰器，并且在定义函数上面@装饰器名称

就是在执行函数之前，执行了装饰器的函数。上述是把foo这个函数以参数的形式传入到装饰器，装饰器进行类型检查，并返回这个被装饰的函数

在上面装饰器中，真正实现作用的代码是下面这3行，检查完后又return回去

```
arg = kwargs[arg_name]
if not isinstance(arg, allowed_type):
    kwargs[arg_name]=allowed_type(kwargs[arg_name])
```

2016年07月02日 于 [linux工匠](http://www.bbotte.com/) 发表



























