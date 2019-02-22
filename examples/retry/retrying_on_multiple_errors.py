from datetime import datetime
from toughpy import *
import random

attempts = 0


@retry(on_error=(TimeoutError, ConnectionError))
def function():
    global attempts
    attempts += 1
    print('Attempt #{} at {}'.format(attempts, datetime.now()))
    raise random.choice([TimeoutError, ConnectionError])()


function()
