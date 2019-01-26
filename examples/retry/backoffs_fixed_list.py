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

# SAMPLE OUTPUT

# Attempt #1 at 2019-01-26 00:07:45.803117
# Attempt #2 at 2019-01-26 00:07:46.103541 (+0.3s)
# Attempt #3 at 2019-01-26 00:07:46.805569 (+0.7s)
# Attempt #4 at 2019-01-26 00:07:47.807780 (+1.0s)
# Attempt #5 at 2019-01-26 00:07:48.813058 (+1.0s)
# Attempt #6 at 2019-01-26 00:07:49.817898 (+1.0s)
# Attempt #7 at 2019-01-26 00:07:50.820509 (+1.0s)
