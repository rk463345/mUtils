import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class watcher:
    def __init__(self, watchDir, sleepTimer=3600):
        self.watchDir = watchDir
        self.sleepTimer = sleepTimer
        self.observer = Observer()

    def run(self):
        event_handler = handler()
        self.observer.schedule(event_handler, self.watchDir, recursive=True)
        self.observer.start()
        try:
            while True:
                # print("starting new cycle of checking")
                time.sleep(self.sleepTimer)
        except:
            self.observer.stop()
            print(f"\nStopping watch on directory {self.watchDir}")
        self.observer.join()


class handler(FileSystemEventHandler):
    def on_created(self, event):
        print(f"FILE :: new file found {event.src_path}")

    def on_deleted(self, event):
        print(f"DELETE :: {event.src_path} deleted")

    def on_moved(self, event):
        print(f"MOVE :: {event.src_path} -> {event.dest_path}")

    def on_any_event(self, event):
        if event.is_directory:
            return None
        else:
            print("ERROR :: an unknown event occured")


if __name__ == "__main__":
    src_path = "/home/beerbin/mdiffer/log"
    watch = watcher()  #TODO Add watch dir
    watch.run()
