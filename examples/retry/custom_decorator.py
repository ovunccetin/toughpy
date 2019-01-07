import tough
from datetime import datetime


class retry_if_none(tough.Retry):
    result_predicate = None
    max_attempts = 10
    backoff = tough.backoffs.FibonacciBackoff(0.1, 0.3)


@retry_if_none
def return_none():
    time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print("Returning None @{0}".format(time))
    return None


return_none()
