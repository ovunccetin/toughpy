from tough import *
from datetime import datetime

import time as t

attempts = 0
prevtime = t.time()

custom_retry = Retry(on_result=None, max_attempts=7, backoff=LinearBackoff(0.3, 0.2))


@custom_retry
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
