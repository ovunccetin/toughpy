from datetime import datetime
from tough import *

attempts = 0


@retry(on_error=TimeoutError)
def function():
    global attempts
    attempts += 1
    print('Attempt #{} at {}'.format(attempts, datetime.now()))
    raise TimeoutError()


function()

