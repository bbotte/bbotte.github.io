# 小议python数据结构的栈及应用

堆栈ADT（abstract data type 抽象数据类型）一般提供以下接口：
Stack()  创建堆栈
push(item)  向栈顶插入项
pop()  返回栈顶的项，并从堆栈中删除该项
clear()  清空堆栈
empty()  判断堆栈是否为空
size()  返回堆栈中项的个数
top()  返回栈顶的项

下面我们写一个栈，并用这个栈检测左右括号是否匹配，因为只有在使用栈的过程中才会了解栈的特点及用法

```python
# coding=utf8
class Stack:
    def __init__(self):
        self.items = []
 
    def isEmpty(self):
        return self.items == []
 
    def push(self, item):
        self.items.append(item)
 
    def pop(self):
        return self.items.pop()
 
    def peek(self):
        return self.items[len(self.items) - 1 ]
 
    def size(self):
        return len(self.items)
 
 
def parChecker(symbolString):
    s = Stack()
    balanced = True
    index = 0
    while index < len(symbolString) and balanced:
        symbol = symbolString[index]
        if symbol == "(":
            s.push(symbol)
        else:
            if s.isEmpty():
                balanced = False
            else:
                s.pop()
        index = index + 1
    if balanced and s.isEmpty():
        return True
    else:
        return False
 
print(parChecker('(())'))
print(parChecker('(()'))
```

结果：

True
False

下面再举一个例子，用栈实现一个包含加减乘除的计算器：

```python
class Node:
    def __init__(self, value):
        self.value = value
        self.next = None
 
class Stack:
    def __init__(self):
        self.top = None
 
    def push(self, value):
        node = Node(value)
        node.next = self.top
        self.top = node
 
    def pop(self):
        node = self.top
        self.top = node.next
        return node.value
 
func_map = {
    '+': lambda x, y: x+y,
    '-': lambda x, y: x-y,
    '*': lambda x, y: x*y,
    '/': lambda x, y: x/y
}
 
def cacl(expr):
    stack = Stack()
    for c in expr:
        if c in '(+-*/':
            stack.push(c)
        elif c.strip() == '':
            pass
        else:
            if c != ')':
                c = int(c)
                if stack.top.value in '+-*/':
                    s = stack.pop()
                    if not isinstance(stack.top.value, (int, float)):
                        raise Exception('wrong expr')
                    v = stack.pop()
                    v = func_map[s](v, c)
                    stack.push(v)
                else:
                    stack.push(c)
            if c == ')':
                if isinstance(stack.top.value, (int, float)):
                    v = stack.pop()
                    if stack.top.value == '(':
                        stack.pop()
                        stack.push(v)
                    else:
                        raise Exception('wrong expr')
                else:
                    raise Exception('wrong expr')
    while stack.top:
        c = stack.pop()
        if not isinstance(c, (int, float)):
            raise Exception('wrong expr')
        if stack.top.value in '+-*/':
            s = stack.pop()
            if not isinstance(stack.top.value, (int, float)):
                raise Exception('wrong expr')
            v = stack.pop()
            v = func_map[s](v, c)
            if stack.top is None:
                return v
            stack.push(v)
        else:
            raise Exception('wrong expr')
 
if __name__ == '__main__':
    print(cacl('(3 + 8) * 3 / ((2 + 4) * 2)'))
```

上述python计算器，在python2.7.10版本中结果只返回整数，而在python3.4.4中结果是float

具体的过程大家断点调试查看更为清晰，有关栈的介绍可以看看这一篇文章

<http://openbookproject.net/thinkcs/python/english3e/stacks.html>

1个学习python的网址 <http://interactivepython.org/runestone/static/pythonds/index.html>

2016年05月04日 于 [linux工匠](http://www.bbotte.com/) 发表



































