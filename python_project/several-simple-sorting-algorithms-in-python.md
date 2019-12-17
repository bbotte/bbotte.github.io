---
layout: default
---

# python几个简单的排序算法

python几个简单的排序算法

矩阵转换，冒泡排序，简单排序，插入排序，打印树

```
#矩阵转换
l1 = [[1,2,3,4],[4,5,6,7],[7,8,9,10]]
result = [[0 for col in range(len(l1))] for row in range(len(l1[0]))]
#for i in range(len(l1)):
#    for j in range(len(l1[0])):
#        result[j][i] = l1[i][j]
 
for i,row in enumerate(result):
    for j,col in enumerate(row):
        result[i][j] = l1[j][i]
print(result)
 
 
#冒泡排序
nums = [9,1,3,2,6]
for i in range(len(nums)):
    flag = False
    for j in range(len(nums)-i-1):
        if nums[j] &gt; nums[j+1]:
            nums[j+1],nums[j] = nums[j],nums[j+1]
            flag = True
    if not flag:
        break
print(nums)
 
 
#简单排序
nums = [9,1,3,2,6]
for i in range(len(nums)):
    minindex = i
    for j in range(i+1,len(nums)):
        if nums[minindex] &gt; nums[j]:
            minindex = j
    if i != minindex:
        nums[i],nums[minindex] = nums[minindex],nums[i]
print(nums)
 
 
#插入排序
nums = [9,1,3,2,6]
sentinel = [0]
new_nums=sentinel+nums
count_swap = 0
count_iter = 0
for i in range(2,len(new_nums)):
    new_nums[0] = new_nums[i]
    for j in reversed(range(1,i)):
        count_iter += 1
        if new_nums[j] &gt; new_nums[0]:
            new_nums[j+1] = new_nums[j]
            new_nums[j] = new_nums[0]
            count_swap += 1
print(nums[1:],count_swap,count_iter)
 
#version 2
my_list = [9,1,3,2,6]
nums = [0] + my_list
count_swap = 0
count_iter = 0
for i in range(2,len(nums)):
    nums[0] = nums[i]
    j = i - 1
    count_iter +=1
    if nums[j] &gt; nums[0]:
        while nums[j] &gt; nums[0]:
            nums[j+1] = nums[j]
            j -= 1
            count_swap += 1
        nums[j+1] = nums[0]
print(nums[1:],count_swap,count_iter)
 
#打印树
import math
def heap_print(lst):
    lengh = len(lst)
    layer = math.ceil(math.log2(lengh)+1)
 
    index = 0
    width = 2 ** layer -1
    for i in range(layer):
        for j in range(2 ** i):
            print('{:^{}}'.format(lst[index],width),end=' ')
            index += 1
            if index &gt;= lengh:
                break
        width = width //2
        #print()
 
lst = [1,2,3,4,5,6,7,8,9]
heap_print(lst)
```

后续再追加

2019年05月16日 于 [linux工匠](http://www.bbotte.com/) 发表







