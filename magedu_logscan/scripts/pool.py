import threading
import logging
import time

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s (%(threadName)-2s) %(message)s')


class ThreadPool:
    def __init__(self, size):
        self.__pool = threading.Semaphore(size)
        self.__threads = []

    def map(self, target, args):
        def inner(arg):
            target(arg)
            self.__pool.release()
        for i, arg in enumerate(args):
            self.__pool.acquire()
            t = threading.Thread(target=inner, args=(arg, ), name='{0}-{1}'.format(target.__name__, i))
            t.start()
            self.__threads.append(t)

    def join(self):
        for t in self.__threads:
            t.join()


def worker(line):
    logging.info(line)
    time.sleep(1)

p = ThreadPool(3)
p.map(worker, range(10))
p.join()