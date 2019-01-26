from tough import *
from datetime import datetime
import time as t

attempts = 0
prevtime = t.time()


@retry(on_result=None, backoff=0.7, max_attempts=5)
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

# Attempt #1 at 2019-01-26 00:07:11.824981
# Attempt #2 at 2019-01-26 00:07:12.527957 (+0.7s)
# Attempt #3 at 2019-01-26 00:07:13.230450 (+0.7s)
# Attempt #4 at 2019-01-26 00:07:13.931037 (+0.7s)
# Attempt #5 at 2019-01-26 00:07:14.634281 (+0.7s)
