from toughpy import *
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

# SAMPLE OUTPUT

# Attempt #1 at 2019-01-26 00:15:25.436719
# Attempt #2 at 2019-01-26 00:15:25.740356 (+0.3s)
# Attempt #3 at 2019-01-26 00:15:26.242885 (+0.5s)
# Attempt #4 at 2019-01-26 00:15:26.943577 (+0.7s)
# Attempt #5 at 2019-01-26 00:15:27.848881 (+0.9s)
# Attempt #6 at 2019-01-26 00:15:28.951370 (+1.1s)
# Attempt #7 at 2019-01-26 00:15:30.256619 (+1.3s)
