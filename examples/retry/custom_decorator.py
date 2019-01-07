from tough import *


class retry_timeout_errors(Retry):
    error_predicate = TimeoutError
    max_attempts = 10
    backoff = backoffs.FibonacciBackoff(0.1, 0.2)
    wrap_error = True


@retry_timeout_errors
def raise_timeout_error():
    print("I'm raising a TimeoutError")
    raise TimeoutError


raise_timeout_error()
