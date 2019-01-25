import time as t
from datetime import datetime

from tough import *

attempts = 0
prevtime = t.time()


@retry(on_result=None, backoff=[0.3, 0.7, 1.0], max_attempts=7)
def function():
    global attempts, prevtime
    attempts += 1
    curr = t.time()

    if attempts == 1:
        print('Attempt #{} at {}'.format(attempts, datetime.now()))
    else:
        elapsed = curr - prevtime
        print('Attempt #{} at {} (+{:.1f}s)'.format(attempts, datetime.now(), elapsed))
        prevtime = curr

    return None


function()
