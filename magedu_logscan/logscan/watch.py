from os import path
from queue import Queue
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from .check import CheckerChain


class Watcher(FileSystemEventHandler):
    def __init__(self, filename, counter):
        self.filename = path.abspath(filename)
        self.queue = Queue()
        self.check_chain = CheckerChain(self.queue, counter)
        self.observer = Observer()
        self.fd = None
        self.offset = 0
        if path.isfile(self.filename):
            self.fd = open(self.filename)
            self.offset = path.getsize(self.filename)

    def on_deleted(self, event):
        if path.abspath(event.src_path) == self.filename:
            self.fd.close()

    def on_moved(self, event):
        if path.abspath(event.src_path) == self.filename:
            self.fd.close()
        if path.abspath(event.dest_path) == self.filename and path.isfile(self.filename):
            self.fd = open(self.filename)
            self.offset = path.getsize(self.filename)

    def on_modified(self, event):
        if path.abspath(event.src_path) == self.filename:
            self.fd.seek(self.offset, 0)
            for line in self.fd:
                line = line.rstrip('\n')
                self.queue.put(line)
            self.offset = self.fd.tell()

    def on_created(self, event):
        if path.abspath(event.src_path) == self.filename and path.isfile(self.filename):
            self.fd = open(self.filename)
            self.offset = path.getsize(self.filename)

    def start(self):
        self.check_chain.start()
        self.observer.schedule(self, path.dirname(self.filename), recursive=False)
        self.observer.start()
        self.observer.join()

    def stop(self):
        self.check_chain.stop()
        self.observer.stop()
        if self.fd is not None and not self.fd.closed:
            self.fd.close()

