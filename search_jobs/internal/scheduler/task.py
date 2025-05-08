from enum import Enum
import time

from batch_jobs.internal.scheduler.time_helpers import time_now_string


class Task:
    def __init__(self, task_name: str):
        self.task_name = task_name

    def internal_init(self, db, current_time, last_successful_run, last_run):
        self.db = db
        self.__current_time = current_time
        self.__last_successful_run = last_successful_run
        self.__last_run = last_run
        print(
            "Internal Init Job",
            self.task_name,
            current_time,
            last_successful_run,
            last_run,
        )

    # internal properties
    @property
    def current_time(self):
        return self.__current_time

    @property
    def last_successful_run(self):
        return self.__last_successful_run

    @property
    def last_run(self):
        return self.__last_run

    # end /internal properties

    def init(self):
        now = time_now_string()
        print("Init Task", self.task_name, now)

    def run(self):
        now = time_now_string()
        print("Running Task...", self.task_name, now)

    def cleanup(self):
        self.db = None
        print("Cleanup Task", self.task_name, time.time())

    def onerror(self):
        print("Error in Task")
