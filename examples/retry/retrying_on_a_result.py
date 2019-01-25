from datetime import datetime
from tough import *

attempts_1 = 0


# Retry on a given result...

@retry(on_result=None)
def function_1():
    global attempts_1
    attempts_1 += 1
    print('Attempt #{} at {}'.format(attempts_1, datetime.now()))
    return None


function_1()
print()

# Retry on a result matching the given predicate...

attempts_2 = 0


@retry(on_result=lambda x: x < 0)
def function_2():
    global attempts_2
    attempts_2 += 1
    print('Attempt #{} at {}'.format(attempts_2, datetime.now()))
    return -1


function_2()
