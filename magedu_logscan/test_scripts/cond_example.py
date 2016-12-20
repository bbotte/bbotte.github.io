import threading
import time
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s [%(threadName)s] %(message)s')

class Message:
    def __init__(self, message):
        self.message = message


def consumer(cond, message):
    with cond:
        cond.wait()
        logging.debug("consumer {0}".format(message.message))


def producer(cond, message):
    with cond:
        time.sleep(2)
        message.message = 'ha ha ha'
        logging.debug("producer {0}".format(message.message))
        cond.notify_all()


if __name__ == '__main__':
    message = Message(None)
    cond = threading.Condition()
    c1 = threading.Thread(target=consumer, args=(cond, message), name='consumer-1')
    c1.start()
    c2 = threading.Thread(target=consumer, args=(cond, message), name='consumer-2')
    c2.start()

    p = threading.Thread(target=producer, args=(cond, message), name='producer')
    p.start()
