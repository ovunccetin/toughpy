import random as r
from abc import abstractmethod
from tough.utils import *

DEFAULT_FIXED_DELAY = 0.5

_msg_invalid_backoff = '''A value of `%s` is not a valid backoff. It should be on of the followings:
 - None to set the default backoff which is 500ms.
 - An instance of on of the Backoff classes (e.g. LinearBackoff, ExponentialBackoff etc.).
 - A number (int or float) to put a fixed delay in seconds (e.g. 1: 1s, 1.2: 1s and 200ms).
 - A list or tuple of numbers as a sequence of delays. (e.g. [1, 2, 5]: 1s + 2s + 5s + 5s + ...)
 - A callable which takes an attempt_number and returns a number which is the delay in seconds.
'''


class Backoff:

    @abstractmethod
    def get_delay(self, attempt_number): pass


class FixedBackoff(Backoff):

    def __init__(self, delay):
        self.delay = delay

    def get_delay(self, attempt_number):
        return self.delay


class FixedListBackoff(Backoff):

    def __init__(self, delay_list):
        self.delays = delay_list

    def get_delay(self, attempt_number):
        size = len(self.delays)
        if attempt_number - 1 < size:
            idx = attempt_number - 1
        else:
            idx = size - 1

        return self.delays[idx]


class RandomBackoff(Backoff):

    def __init__(self, min_seconds, max_seconds):
        self.min_seconds = min_seconds
        self.max_seconds = max_seconds

    def get_delay(self, attempt_number=None):
        lower_bound = int(self.min_seconds * 1000)
        upper_bound = int(self.max_seconds * 1000)

        random_millis = r.randint(lower_bound, upper_bound)
        return float(random_millis) / 1000


class LinearBackoff(Backoff):

    def __init__(self, initial_delay, increase, randomizer=None):
        self.initial_delay = initial_delay
        self.increase = increase
        self.randomizer = _get_randomizer_func(randomizer)

    def get_delay(self, attempt_number):
        return self.initial_delay + self.increase * (attempt_number - 1) + self.randomizer()


class ExponentialBackoff(Backoff):

    def __init__(self, initial_delay, base=2, randomizer=None):
        self.initial_delay = initial_delay
        self.base = base
        self.randomizer = _get_randomizer_func(randomizer)

    def get_delay(self, attempt_number):
        return self.initial_delay * self.base ** (attempt_number - 1) + self.randomizer()


class FibonacciBackoff(FixedListBackoff):

    def __init__(self, first, second, n_max=16):
        fibs = [first, second]
        for i in range(2, n_max + 1):
            fibs.append(fibs[-1] + fibs[-2])

        super().__init__(fibs)


class _CallableBackoff(Backoff):

    def __init__(self, func):
        self._func = func

    def get_delay(self, attempt_number):
        return self._func(attempt_number)


def create_backoff(given, default=None):
    if isinstance(given, Backoff):
        result = given
    elif given is None:
        default_delay = DEFAULT_FIXED_DELAY if default is None else default
        result = create_backoff(given=default_delay)
    elif is_number(given):
        result = FixedBackoff(given)
    elif is_list_or_tuple_of_numbers(given):
        result = FixedListBackoff(given)
    elif callable(given):
        result = _CallableBackoff(given)
    else:
        raise ValueError(_msg_invalid_backoff % type(given).__name__)

    return result


def __fn_zero():
    return 0


def _get_randomizer_func(rnd):
    if callable(rnd):
        fn = rnd
    elif isinstance(rnd, tuple):
        fn = RandomBackoff(rnd[0], rnd[1]).get_delay
    else:
        fn = __fn_zero

    return fn


def _get_attempt_no(kwargs):
    return kwargs['attempt_no']


__all__ = [
    'Backoff',
    'FixedBackoff',
    'FixedListBackoff',
    'LinearBackoff',
    'RandomBackoff',
    'ExponentialBackoff',
    'FibonacciBackoff',
    'DEFAULT_FIXED_DELAY'
]
