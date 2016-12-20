import logging
import threading
import time


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s (%(threadName)-2s) %(message)s')


class Message:
    def __init__(self):
        self.message = None


def consumer(cond, message):
    with cond:
        cond.wait()
        logging.info(message.message)


def producer(cond, message):
    with cond:
        message.message = "this is message"
        cond.notify_all()

if __name__ == '__main__':
    cond = threading.Condition()
    message = Message()
    c1 = threading.Thread(name='c1', target=consumer, args=(cond, message))
    c2 = threading.Thread(name='c2', target=consumer, args=(cond, message))
    p = threading.Thread(name='p', target=producer, args=(cond, message))

    c1.start()
    time.sleep(0.2)
    c2.start()
    time.sleep(0.2)
    p.start()
