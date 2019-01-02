import random as r


# TODO write unit tests for backoff functions

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

        millis = r.randint(lower_bound, upper_bound)
        return float(millis) / 1000

    return _get


def linear(initial, accrual, rnd=None):
    rnd_fn = _get_rnd_fn(rnd)

    def _get(attempt_no):
        return initial + accrual * (attempt_no - 1) + rnd_fn()

    return _get


def exponential(initial, base=2, rnd=None):
    rnd_fn = _get_rnd_fn(rnd)

    def _get(attempt_no):
        return initial * base ** (attempt_no - 1) + rnd_fn()

    return _get


def _get_rnd_fn(rnd):
    if callable(rnd):
        fn = rnd
    elif isinstance(rnd, tuple):
        fn = random(rnd[0], rnd[1])
    else:
        fn = lambda: 0

    return fn


def _get_attempt_no(kwargs):
    return kwargs['attempt_no']