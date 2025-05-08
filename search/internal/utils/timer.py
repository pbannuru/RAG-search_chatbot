import time
from datetime import datetime


class Timer:
    def __init__(self):
        self.start = 0.0
        self.end = 0.0

    def start_timer(self):
        self.start = time.perf_counter()
        return self

    def end_timer(self):
        self.end = time.perf_counter()
        return self

    @property
    def elapsed_time(self) -> float:
        return self.end - self.start

    @property
    def elapsed_time_ms(self):
        return int(self.elapsed_time * 1000)

    @property
    def start_time_string(self):
        return datetime.fromtimestamp(self.start).strftime("%Y-%m-%d %H:%M:%S")
