import threading
import logging
import time

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s [%(threadName)s] %(message)s')


def worker(event):
    event.wait(3)
    logging.debug("event is set")


def set(event):
    time.sleep(2)
    event.set()
    logging.debug("event is set")


if __name__ == '__main__':
    event = threading.Event()

    w = threading.Thread(target=worker, args=(event, ), name='worker')
    w.start()

    s = threading.Thread(target=set, args=(event, ), name='set')
    s.start()
