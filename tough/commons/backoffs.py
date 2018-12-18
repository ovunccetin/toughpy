import random as r

# TODO write unit tests for backoff functions

def fixed(delay):
    # noinspection PyUnusedLocal
    def _get(*args, **kwargs):
        return delay

    return _get


def fixed_list(delay_list):
    length = len(delay_list)

    # noinspection PyUnusedLocal
    def _get_delay(*args, **kwargs):
        attempt_no = _get_attempt_no(kwargs)
        if attempt_no - 1 < length:
            idx = attempt_no - 1
        else:
            idx = length - 1

        return delay_list[idx]

    return _get_delay


def random(min_sec, max_sec):
    # noinspection PyUnusedLocal
    def _get(*args, **kwargs):
        lb = int(min_sec * 1000)
        ub = int(max_sec * 1000)

        ms = r.randint(lb, ub)
        return float(ms) / 1000

    return _get


def linear(initial, accrual, rnd=None):
    rnd_fn = _get_rnd_fn(rnd)

    # noinspection PyUnusedLocal
    def _get(*args, **kwargs):
        attempt_no = _get_attempt_no(kwargs)
        return initial + accrual * (attempt_no - 1) + rnd_fn()

    return _get


def exponential(initial, exp_base=2, rnd=None):
    rnd_fn = _get_rnd_fn(rnd)

    # noinspection PyUnusedLocal
    def _get(*args, **kwargs):
        attempt_no = _get_attempt_no(kwargs)
        return initial * exp_base ** (attempt_no - 1) + rnd_fn()

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