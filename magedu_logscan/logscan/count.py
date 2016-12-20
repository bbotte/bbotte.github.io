import threading
import shelve


class Counter:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db = shelve.open(self.db_path, 'c')
        self.lock = threading.Lock()
        self.stopped = False

    def inc(self, name):
        with self.lock:
            self.db[name] = self.db.get(name, 0) + 1

    def get(self, name):
        with self.lock:
            self.db.get(name, 0)

    def clean(self, name):
        with self.lock:
            self.db.pop(name)

    def stop(self):
        with self.lock:
            if not self.stopped:
                self.db.close()

