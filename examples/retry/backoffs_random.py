from tough import *
from datetime import datetime
import time as t

attempts = 0
prevtime = t.time()


@retry(on_result=None, backoff=RandomBackoff(0.15, 1.2), max_attempts=7)
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

# Attempt #1 at 2019-01-26 00:11:09.609079
# Attempt #2 at 2019-01-26 00:11:10.760337 (+1.151s)
# Attempt #3 at 2019-01-26 00:11:11.158994 (+0.399s)
# Attempt #4 at 2019-01-26 00:11:11.744030 (+0.585s)
# Attempt #5 at 2019-01-26 00:11:11.964911 (+0.221s)
# Attempt #6 at 2019-01-26 00:11:12.857197 (+0.892s)
# Attempt #7 at 2019-01-26 00:11:13.649822 (+0.793s)
