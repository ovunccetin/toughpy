from toughpy import *
from datetime import datetime
import time as t

attempts = 0
prevtime = t.time()


# Retrying with default configuration:
#  - Retry on any error type
#  - Max attempts are 3
#  - Backoff is 0.5 seconds between each attempt

@retry
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

    raise Exception()


function()

# SAMPLE OUTPUT

# Attempt #1 at 2019-01-26 00:13:22.572580
# Attempt #2 at 2019-01-26 00:13:23.076715 (+0.5s)
# Attempt #3 at 2019-01-26 00:13:23.579120 (+0.5s)
# Traceback (most recent call last):
#   File "toughpy/examples/retry/basic_retry.py", line 29, in <module>
#     function()
#   ...
