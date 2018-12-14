import time
from toughpy.utils import StateError
from .duration import *

_1M = 1000000

# TODO count the number of start-stops, add metrics like total_time, count, max_time, min_time, average_time

class Stopwatch:
    @classmethod
    def create_started(cls, name=None):
        return cls(name).start()

    def __init__(self, name=None):
        self._name = name
        self._start_time = None
        self._running = False
        self._elapsed_micros = 0

    def is_running(self):
        return self._running

    def start(self):
        if self.is_running():
            raise StateError('Stopwatch `%s` is already running.' % self._name)

        self._running = True
        self._start_time = _current_micros()

        return self

    def stop(self):
        end = _current_micros()

        if not self.is_running():
            raise StateError('Stopwatch `%s` is already stopped.')

        self._elapsed_micros += end - self._start_time

        return self

    def reset(self):
        self._elapsed_micros = 0
        self._start_time = None
        self._running = False

        return self

    def elapsed_micros(self):
        if self.is_running():
            return _current_micros() - self._start_time + self._elapsed_micros
        else:
            return self._elapsed_micros

    def elapsed_millis(self):
        return microseconds.to_milliseconds(self.elapsed_micros())

    def elapsed_seconds(self):
        return microseconds.to_seconds(self.elapsed_micros())

    def elapsed_time(self):
        return Duration(self.elapsed_micros(), microseconds)


def _current_micros():
    return time.time() * _1M
