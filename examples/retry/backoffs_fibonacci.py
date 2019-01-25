from tough import *
from datetime import datetime
import time as t

attempts = 0
prevtime = t.time()


@retry(on_result=None, backoff=FibonacciBackoff(0.1, 0.2), max_attempts=9)
def function():
    global attempts, prevtime
    attempts += 1
    curr = t.time()

    if attempts == 1:
        print('Attempt #{} at {}'.format(attempts, datetime.now()))
    else:
        elapsed = curr - prevtime
        print('Attempt #{} at {} (+{:.3f}s)'.format(attempts, datetime.now(), elapsed))
        prevtime = curr

    return None


function()
