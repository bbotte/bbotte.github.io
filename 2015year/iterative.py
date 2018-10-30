#!/usr/bin/env python
import time
from functools import wraps

def timer(function):
    @wraps(function)
    def function_timer(*args, **kwargs):
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        print('total time: {0}'.format(str(t1-t0)))
        return result
    return function_timer

@timer
def factorial(number):
    product = 1 
    for i in range(number):
        product = product * (i+1)
    return product

if __name__ == "__main__":
   factorial(200)
