import threading
import logging
import time

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s [%(threadName)s] %(message)s')


def worker(lock):
    with lock:
        logging.debug("ha ha ha ")

if __name__ == '__main__':
    lock = threading.Lock()
    t1 = threading.Thread(target=worker, name='t1', args=(lock, ))
    t1.start()
    t2 = threading.Thread(target=worker, name='t2', args=(lock, ))
    t2.start()
