from tough import *
from datetime import datetime

import time as t

attempts = 0
prevtime = t.time()


def custom_retry(max_retries):
    return Retry(on_result=None, max_attempts=max_retries + 1, backoff=LinearBackoff(0.3, 0.2))


@custom_retry(max_retries=3)
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
