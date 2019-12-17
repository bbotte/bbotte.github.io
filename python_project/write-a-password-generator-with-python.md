---
layout: default
---

# 用python写一个复杂密码生成器

我们来用python写一个密码生成器，用random随机从a-z挑选，实现随机数第一版：

```
# cat pass1.py
#!/usr/bin/env python
#
import random
 
alphabet = "abcdefghijklmnopqrstuvwxyz"
pw_length = 8
mypw = ""
 
for _ in range(pw_length):
    next_index = random.randrange(len(alphabet))
    mypw = mypw + alphabet[next_index]
print(mypw)
 
 
'''
randrange(self, start, stop=None, step=1, int=<type 'int'>, default=None, maxwidth=9007199254740992L) 
method of random.Random instance
'''
```

为了增加密码的强度，需要把小写字母改为大小写+数字的

alphabet = “abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ”

ok，这样生成出来的密码虽然强度增大了一些，不过为了保证我们会有至少一个大写字母和小写字母，那么首先生成一个小写字母的密码，然后随机选择一个或多个大写字母来代替其中一个字母，或者来用一个数字代替一个或多个字母

```
#!/usr/bin/env python
# coding=utf8
import random
 
alphabet = "abcdefghijklmnopqrstuvwxyz"
pw_length = 8
mypw = ""
 
for _ in range(pw_length):
    next_index = random.randrange(len(alphabet))
    mypw = mypw + alphabet[next_index]
 
#替换一个或两个字母为数字
for _ in range(random.randrange(1,3)):
    replace_index = random.randrange(len(mypw)//2)
    mypw = mypw[0:replace_index] + str(random.randrange(10)) + mypw[replace_index+1:]
 
#替换一个或两个字母为大写
for _ in range(random.randrange(1,3)):
    replace_index = random.randrange(len(mypw)//2, len(mypw))
    mypw = mypw[0:replace_index] + mypw[replace_index].upper() + mypw[replace_index+1:]
print(mypw)
```

```
# for i in {1..10};do ./pass2.py ;done
72smWufz
u4nidLnK
1j9tkqzS
7hnozWHt
7clgSCtp
66acRmnz
fh9iLknv
v3cdoXtr
ah83tUcV
7d0rARlc
```

上述python脚本用len(mypw)//2作为获取范围的一个点，保证第一步和第二步只取第一个for循环生成mypw一半的范围

```
mypw = mypw[0:replace_index] + str(random.randrange(10)) + mypw[replace_index+1:]
```

这一步把str(random.randrange(10))的值嵌入到生成的mypw字符串中，下面同理，由此生成的密码数字都在前面，而大写都在后面，如果再随机一些，数字、小写、大写不按顺序排列呢，下面第三版用shuffle(洗牌，混乱)方法：

```
#!/usr/bin/env python
import random
 
alphabet = "abcdefghijklmnopqrstuvwxyz"
upperalphabet = alphabet.upper()
pw_len = 8
pwlist = []
 
for _ in range(pw_len//3):
    pwlist.append(alphabet[random.randrange(len(alphabet))])
    pwlist.append(upperalphabet[random.randrange(len(upperalphabet))])
    pwlist.append(str(random.randrange(10)))
for _ in range(pw_len - len(pwlist)):
    pwlist.append(alphabet[random.randrange(len(alphabet))])
 
random.shuffle(pwlist)
pwstring = "".join(pwlist)
print(pwstring)
 
 
'''
shuffle(self, x, random=None, int=<type 'int'>) method of random.Random instance
    x, random=random.random -> shuffle list x in place; return None.
'''
```

```
# for i in {1..10};do ./pass3.py ;done
aAa2aO6y
Cyu54eYt
xapB3X1n
aBQ7sb7v
iT9rdJ9y
3fkmD4Ki
4ln3vEWp
7evC3Cks
1A2itXxt
V7grHw3h
```

上面代码的第一个循环是生成小写、大写、数字的列表，第二个循环是因为密码长度不是3的整数倍，而后面空了2个位置，这时把后面2个空位补上。最后由shuffle方法处理，生成大小写和数字相混合的密码。

译自<http://interactivepython.org/runestone/static/everyday/2013/01/3_password.html> 

2016年05月12日 于 [linux工匠](http://www.bbotte.com/) 发表







