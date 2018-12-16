import random as r


def fixed(delay):
    # noinspection PyUnusedLocal
    def _get(**kwargs):
        return delay

    return _get


def random(min_sec, max_sec):
    # noinspection PyUnusedLocal
    def _get(**kwargs):
        lb = int(min_sec * 1000)
        ub = int(max_sec * 1000)

        ms = r.randint(lb, ub)
        return float(ms) / 1000

    return _get


def linear(initial, accrual, rnd=None):
    rnd_fn = _get_rnd_fn(rnd)

    # noinspection PyUnusedLocal
    def _get(**kwargs):
        attempt_number = kwargs['attempt']

        return initial + accrual * (attempt_number - 1) + rnd_fn()

    return _get


def exponential(initial, exp_base=2, rnd=None):
    rnd_fn = _get_rnd_fn(rnd)

    def _get(**kwargs):
        attempt_number = kwargs['attempt']
        return initial * exp_base ** (attempt_number - 1) + rnd_fn()

    return _get


def _get_rnd_fn(rnd):
    if callable(rnd):
        fn = rnd
    elif isinstance(rnd, tuple):
        fn = random(rnd[0], rnd[1])
    else:
        fn = lambda: 0

    return fn
