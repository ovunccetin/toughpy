from tough import *
from datetime import datetime
import time as t

attempts_1 = 0
prevtime_1 = t.time()

print('Without randomizer...')


@retry(on_result=None,
       backoff=LinearBackoff(initial_delay=0.1, increase=0.2),
       max_attempts=7)
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
       backoff=LinearBackoff(initial_delay=0.1, increase=0.2, randomizer=(0.01, 0.08)),
       max_attempts=7)
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

# SAMPLE OUTPUT

# Without randomizer...
#   Attempt #1 at 2019-01-26 00:10:16.470130
#   Attempt #2 at 2019-01-26 00:10:16.575375 (+0.11s)
#   Attempt #3 at 2019-01-26 00:10:16.879167 (+0.30s)
#   Attempt #4 at 2019-01-26 00:10:17.383652 (+0.50s)
#   Attempt #5 at 2019-01-26 00:10:18.087912 (+0.70s)
#   Attempt #6 at 2019-01-26 00:10:18.993266 (+0.91s)
#   Attempt #7 at 2019-01-26 00:10:20.096257 (+1.10s)
#
# With randomizer...
#   Attempt #1 at 2019-01-26 00:10:20.096471
#   Attempt #2 at 2019-01-26 00:10:20.255172 (+0.16s)
#   Attempt #3 at 2019-01-26 00:10:20.630572 (+0.38s)
#   Attempt #4 at 2019-01-26 00:10:21.158550 (+0.53s)
#   Attempt #5 at 2019-01-26 00:10:21.929264 (+0.77s)
#   Attempt #6 at 2019-01-26 00:10:22.892092 (+0.96s)
#   Attempt #7 at 2019-01-26 00:10:24.012547 (+1.12s)
