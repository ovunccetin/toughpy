from tough import *
from datetime import datetime
from random import randint


def is_negative(x):
    return x < 0


def is_positive(x):
    return x > 0


# A custom decorator to retry if the returned value is negative
retry_if_negative = Retry(on_result=is_negative, max_attempts=5, backoff=LinearBackoff(1, 0.5))


@retry_if_negative
def mostly_negative():
    rnd = randint(-20, 3)
    print(' - Random generated {} at {}'.format(rnd, datetime.now().time()))
    return rnd


print('Mostly Negative')
mostly_negative()


# Another decorator which takes the max number of retries as a function parameter
def retry_if_positive(max_retries):
    return Retry(on_result=is_positive, backoff=ExponentialBackoff(0.5), max_attempts=max_retries + 1)


@retry_if_positive(max_retries=4)
def mostly_positive():
    rnd = randint(-3, 20)
    print(' - Random generated {} at {}'.format(rnd, datetime.now().time()))
    return rnd


print('\nMostly Positive')
mostly_positive()
