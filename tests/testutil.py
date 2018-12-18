import contextlib as clib
import time


@clib.contextmanager
def silence():
    try:
        yield
    except:
        pass

class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.elapsed = self.end - self.start

def timeit(fn):
    start = time.time()
    with silence():
        fn()
    end = time.time()

    return end - start


def assert_close_to(actual, expected, delta=0.1):
    assert expected - delta <= actual <= expected + delta, \
        '%s is not close to %s with delta ±%s' % (actual, expected, delta)
