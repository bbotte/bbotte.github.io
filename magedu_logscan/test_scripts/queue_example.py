import threading
from queue import Queue
import time
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s [%(threadName)s] %(message)s')


def consumer(e, q):
    while not e.is_set():
        message = q.get()
        time.sleep(0.1)
        logging.debug('consume {0}'.format(message))


def producer(e, q):
    for i in range(10):
        q.put(i)
        time.sleep(0.1)
        logging.debug('produce {0}'.format(i))
    if q.empty():
        e.set()


if __name__ == '__main__':
    e = threading.Event()
    q = Queue(maxsize=10)

    for i in range(5):
        #q.put(i, block=True, timeout=1)
        q.put_nowait(i)
        logging.debug(i)

    for _ in range(10):
        logging.debug(q.get_nowait())

    # c1 = threading.Thread(target=consumer, args=(e, q), name='consumer-1')
    # c1.start()
    # c2 = threading.Thread(target=consumer, args=(e, q), name='consumer-2')
    # c2.start()
    #
    # p = threading.Thread(target=producer, args=(e, q), name='producer')
    # p.start()