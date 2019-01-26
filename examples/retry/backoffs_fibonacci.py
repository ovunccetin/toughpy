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

# SAMPLE OUTPUT

# Attempt #1 at 2019-01-26 00:06:35.644605
# Attempt #2 at 2019-01-26 00:06:35.745339 (+0.101s)
# Attempt #3 at 2019-01-26 00:06:35.946478 (+0.201s)
# Attempt #4 at 2019-01-26 00:06:36.246947 (+0.300s)
# Attempt #5 at 2019-01-26 00:06:36.750821 (+0.504s)
# Attempt #6 at 2019-01-26 00:06:37.552984 (+0.802s)
# Attempt #7 at 2019-01-26 00:06:38.858256 (+1.305s)
# Attempt #8 at 2019-01-26 00:06:40.963567 (+2.105s)
# Attempt #9 at 2019-01-26 00:06:44.368571 (+3.405s)
