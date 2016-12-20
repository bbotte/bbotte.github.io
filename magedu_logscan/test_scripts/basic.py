import threading
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s [%(threadName)s] %(message)s')


def worker(message):
    logging.debug("worker is started, {0}".format(message))


if __name__ == '__main__':
    #t = threading.Thread(target=worker, name='worker', args=('ha ha ha', ))
    t = threading.Thread(target=worker, name='worker', kwargs={'message': 'ha ha ha'})
    t.daemon = True
    t.start()
    t.join(2)
    logging.debug('main thread exiting')
