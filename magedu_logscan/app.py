from logscan.match import Matcher
from logscan.watch import Watcher
from logscan.schedule import Schedule

if __name__ == '__main__':
    import sys
    sched = Schedule()
    try:
        sched.add_watcher(Watcher(sys.argv[1], Matcher('#123#')))
        sched.add_watcher(Watcher(sys.argv[2], Matcher('#123#')))
        sched.join()
    except KeyboardInterrupt:
        sched.remove_watcher(sys.argv[1])
        sched.remove_watcher(sys.argv[2])
    sched.join()
