import random as r
from .utils import *

DEFAULT_FIXED_DELAY = 0.5

_msg_invalid_backoff = '''A value of `%s` is not a valid backoff. It should be on of the followings:
 - Missing or None to set the default delay which is 500ms.
 - A number (int or float) to put a fixed delay in seconds (e.g. 1: 1s, 1.2: 1s and 200ms).
 - A list or tuple of numbers as a sequence of delays. (e.g. [1, 2, 5]: 1s + 2s + 5s + 5s + ...)
 - A callable (e.g. a function) taking the previous Attempt object and returning a number which is the delay in seconds.
'''


def fixed(delay):
    def _get(attempt_no=None):
        return delay

    return _get


def fixed_list(delay_list):
    length = len(delay_list)

    def _get_delay(attempt_no):
        if attempt_no - 1 < length:
            idx = attempt_no - 1
        else:
            idx = length - 1

        return delay_list[idx]

    return _get_delay


def random(min_sec, max_sec):
    def _get(attempt_no=None):
        lower_bound = int(min_sec * 1000)
        upper_bound = int(max_sec * 1000)

        random_millis = r.randint(lower_bound, upper_bound)
        return float(random_millis) / 1000

    return _get


def linear(initial, accrual, randomizer=None):
    rnd_fn = _get_rnd_fn(randomizer)

    def _get(attempt_no):
        return initial + accrual * (attempt_no - 1) + rnd_fn()

    return _get


def exponential(initial, base=2, randomizer=None):
    rnd_fn = _get_rnd_fn(randomizer)

    def _get(attempt_no):
        return initial * base ** (attempt_no - 1) + rnd_fn()

    return _get


def create_backoff_func(given):
    if given is None:
        result = fixed(DEFAULT_FIXED_DELAY)
    elif is_number(given):
        result = fixed(given)
    elif is_list_or_tuple_of_numbers(given):
        result = fixed_list(given)
    elif callable(given):
        result = given
    else:
        raise ValueError(_msg_invalid_backoff % type(given).__name__)

    return result


def __fn_zero():
    return 0


def _get_rnd_fn(rnd):
    if callable(rnd):
        fn = rnd
    elif isinstance(rnd, tuple):
        fn = random(rnd[0], rnd[1])
    else:
        fn = __fn_zero

    return fn


def _get_attempt_no(kwargs):
    return kwargs['attempt_no']
