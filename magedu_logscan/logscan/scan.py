import base64
import os
import json
from .schedule import Schedule
from .check import Checker


class Scan:
    def __init__(self, config_dir):
        # /config_dir/path/{name}.json
        self.config_dir = config_dir
        self.schedule = Schedule('/tmp/counter.db')

    def get_config(self):
        for path in os.listdir(self.config_dir):
            if os.path.isdir(path):
                filename = base64.urlsafe_b64decode(os.path.basename(path))
                self.schedule.make_watcher(filename)
                for cfg in os.listdir('/'.join(self.config_dir, path)):
                    with open('/'.join((self.config_dir, path, cfg))) as f:
                        rule = json.load(f)
                        checker = Checker(**rule)
                        self.schedule.watchers[filename].check_chain.add_checker(checker)