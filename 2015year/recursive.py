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
    def _factorial(number):
        if number <= 1:
            return 1
        else:
            return number * _factorial(number-1)
    return _factorial(number)

if __name__ == "__main__":
    factorial(200)

