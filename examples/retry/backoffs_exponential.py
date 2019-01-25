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
