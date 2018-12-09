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