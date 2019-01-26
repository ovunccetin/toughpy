from tough import *
from datetime import datetime
import time as t

attempts_1 = 0
prevtime_1 = t.time()

print('Without randomizer...')


@retry(on_result=None,
       backoff=ExponentialBackoff(initial_delay=0.1),
       max_attempts=6)
def function_1():
    global attempts_1, prevtime_1
    attempts_1 += 1
    curr = t.time()

    if attempts_1 == 1:
        print('  Attempt #{} at {}'.format(attempts_1, datetime.now()))
    else:
        elapsed = curr - prevtime_1
        print('  Attempt #{} at {} (+{:.2f}s)'.format(attempts_1, datetime.now(), elapsed))
        prevtime_1 = curr

    return None


function_1()

print('\nWith randomizer...')

attempts_2 = 0
prevtime_2 = t.time()


@retry(on_result=None,
       backoff=ExponentialBackoff(initial_delay=0.1, randomizer=(0.01, 0.08)),
       max_attempts=6)
def function_2():
    global attempts_2, prevtime_2
    attempts_2 += 1
    curr = t.time()

    if attempts_2 == 1:
        print('  Attempt #{} at {}'.format(attempts_2, datetime.now()))
    else:
        elapsed = curr - prevtime_2
        print('  Attempt #{} at {} (+{:.2f}s)'.format(attempts_2, datetime.now(), elapsed))
        prevtime_2 = curr

    return None


function_2()

print('\nWith base=3...')

attempts_3 = 0
prevtime_3 = t.time()


@retry(on_result=None,
       backoff=ExponentialBackoff(initial_delay=0.1, base=3),
       max_attempts=6)
def function_2():
    global attempts_3, prevtime_3
    attempts_3 += 1
    curr = t.time()

    if attempts_3 == 1:
        print('  Attempt #{} at {}'.format(attempts_3, datetime.now()))
    else:
        elapsed = curr - prevtime_3
        print('  Attempt #{} at {} (+{:.2f}s)'.format(attempts_3, datetime.now(), elapsed))
        prevtime_3 = curr

    return None


function_2()

# SAMPLE OUTPUT

# Without randomizer...
#   Attempt #1 at 2019-01-26 00:04:19.279495
#   Attempt #2 at 2019-01-26 00:04:19.382463 (+0.10s)
#   Attempt #3 at 2019-01-26 00:04:19.583803 (+0.20s)
#   Attempt #4 at 2019-01-26 00:04:19.989167 (+0.41s)
#   Attempt #5 at 2019-01-26 00:04:20.792841 (+0.80s)
#   Attempt #6 at 2019-01-26 00:04:22.393364 (+1.60s)
#
# With randomizer...
#   Attempt #1 at 2019-01-26 00:04:22.393624
#   Attempt #2 at 2019-01-26 00:04:22.535514 (+0.14s)
#   Attempt #3 at 2019-01-26 00:04:22.809249 (+0.27s)
#   Attempt #4 at 2019-01-26 00:04:23.268458 (+0.46s)
#   Attempt #5 at 2019-01-26 00:04:24.108725 (+0.84s)
#   Attempt #6 at 2019-01-26 00:04:25.755111 (+1.65s)
#
# With base=3...
#   Attempt #1 at 2019-01-26 00:04:25.755383
#   Attempt #2 at 2019-01-26 00:04:25.855563 (+0.10s)
#   Attempt #3 at 2019-01-26 00:04:26.157341 (+0.30s)
#   Attempt #4 at 2019-01-26 00:04:27.059294 (+0.90s)
#   Attempt #5 at 2019-01-26 00:04:29.764658 (+2.71s)
#   Attempt #6 at 2019-01-26 00:04:37.865328 (+8.10s)
