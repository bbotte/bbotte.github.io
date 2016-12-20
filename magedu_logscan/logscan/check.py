import threading
import logging
from queue import Queue, Full
from .match import Matcher
from .notification import Message


class Checker:
    def __init__(self, name, expr, path, interval, threshold, users, counter, notification):
        self.name = name
        self.expr = expr
        self.path = path
        self.interval = interval
        self.threshold = threshold
        self.users = users
        self.counter = counter
        self.__event = threading.Event()
        self.notification = notification
        self.matcher = Matcher(name, expr)

    def check(self):
        while not self.__event.is_set():
            self.__event.wait(self.interval * 60)
            count = self.counter.get(name=self.name)
            self.counter.clean(self.name)
            if count >= self.threshold[0]:
                if count < self.threshold[1] or self.threshold[1] < 0:
                    self.notify('{0} matched {1} times in {2}min'.format(self.name, count, self.interval))

    def start(self):
        threading.Thread(self.check, name='checker-{0}'.format(self.name)).start()

    def notify(self, count):
        for user in self.users:
            message = Message(user, self.name, self.path, count)
            self.notification.notify(message)

    def stop(self):
        self.__event.set()


class CheckerChain:
    def __init__(self, queue, counter):
        self.queue = queue
        self.counter = counter
        self.checkers = {}
        self.queues = {}
        self.events = {}
        self.line = None
        self.__event = threading.Event()
        self.__cond = threading.Condition()

    def _match(self, checker):
        while not self.events[checker.name].is_set():
            line = self.queues[checker.name]
            if self.checkers[checker.name].matcher.match(line):
                self.counter.inc(checker.name)

    def match(self, checker):
        queue = Queue()
        self.queues[checker.name] = queue
        threading.Thread(target=self._match, args=(checker, )).start()
        while not self.events[checker.name].is_set():
            with self.__cond:
                self.__cond.wait()
                try:
                    queue.put_nowait(self.line)
                except Full:
                    logging.error("match queue for {0} full".format(checker.name))

    def add_checker(self, checker):
        self.checkers[checker.name] = checker
        checker.start()
        event = threading.Event()
        self.events[checker.name] = event
        threading.Thread(target=self.match, args=(checker, )).start()

    def remove_checker(self, name):
        if name in self.events.keys():
            self.events[name].set()
            self.checkers[name].stop()
            self.events.pop(name)
            self.checkers.pop(name)

    def start(self):
        while not self.__event.is_set():
            self.line = self.queue.get()
            self.__cond.notify_all()

    def stop(self):
        self.__event.set()
        for k, e in self.events.values():
            e.set()
            self.checkers[k].stop()