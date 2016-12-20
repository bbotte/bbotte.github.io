import threading
from os import path
from .count import Counter
from .notification import Notification
from .watch import Watcher


class Schedule:
    def __init__(self, counter_path):
        self.watchers = {}
        self.threads = {}
        self.counter = Counter(counter_path)
        self.notification = Notification()
        self.notification.start()

    def make_watcher(self, filename):
        watcher = Watcher(filename, self.counter)
        self.add_watcher(watcher)

    def add_watcher(self, watcher):
        if watcher.filename not in self.watchers.keys():
            watcher.counter = self.counter
            t = threading.Thread(target=watcher.start, name='Watcher-{0}'.format(watcher.filename))
            t.daemon = True
            t.start()
            self.threads[watcher.filename] = t
            self.watchers[watcher.filename] = watcher

    def remove_watcher(self, filename):
        key = path.abspath(filename)
        if key in self.watchers.keys():
            self.watchers[key].stop()
            self.watchers.pop(key)
            self.threads.pop(key)

    def join(self):
        while self.watchers.values():
            for t in list(self.threads.values()):
                t.join()

    def stop(self):
        for w in self.watchers.values():
            w.stop()
        self.counter.stop()
        self.notification.stop()
