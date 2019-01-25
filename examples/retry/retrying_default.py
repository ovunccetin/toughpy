from tough import *
from datetime import datetime

attempts = 0


# Retrying with default configuration:
#  - Retry any error type
#  - Max attempts are 3
#  - Backoff is 0.5 seconds between each attempt

@retry
def function():
    global attempts
    attempts += 1
    print('Attempt #{} at {}'.format(attempts, datetime.now()))
    raise Exception()


function()
