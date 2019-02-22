from toughpy import *
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

# SAMPLE OUTPUT

# Attempt #1 at 2019-01-26 00:15:47.237935
# Attempt #2 at 2019-01-26 00:15:47.542465 (+0.3s)
# Attempt #3 at 2019-01-26 00:15:48.047214 (+0.5s)
# Attempt #4 at 2019-01-26 00:15:48.750627 (+0.7s)
