import contextlib as clib
import time


@clib.contextmanager
def silence():
    try:
        yield
    except:
        pass


def timeit(fn):
    start = time.time()
    with silence(): fn()
    end = time.time()

    return end - start


def assert_close_to(actual, expected, delta=0.1):
    assert expected - delta <= actual <= expected + delta, \
        '%s is not close to %s with delta ±%s' % (actual, expected, delta)
