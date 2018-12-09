import toughpy.utils as util
from toughpy.utils import UNDEFINED
import six
import sys
import time
import random

__msg_invalid_max_attempts = '`%s` is not a valid value for `max_attempts`. It should be an integer greater than 0.'

__msg_invalid_retry_on_error = '''A value of `%s` is not valid for `retry_on_error`. It should be one of the followings:
 - Missing or None to set to the default value (i.e. retry on any error)
 - An error type, e.g. ConnectionError
 - A tuple of error types, e.g. (ConnectionError, TimeoutError)
 - A list of error types, e.g. [ConnectionError, TimeoutError]
 - A set of error types, e.g. {ConnectionError, TimeoutError}
 - A callable (e.g. a function) taking the result of the previous call and returning a boolean.
'''

__msg_invalid_backoff = '''A value of `%s` is not valid for `backoff`. It should be on of the followings:
 - Missing or None to set the default delay.
 - An integer to put a fixed delay in seconds (e.g. 1 means 1 second).
 - A float to put a fixed delay in seconds (e.g. 1.3 means 1 second and 300 milliseconds)
 - A callable (e.g. a function) taking the previous Attempt object and returning a number which is the delay in seconds.
'''


# Built-in Retry Conditions

def _retry_on_any_error(error):
    return isinstance(error, BaseException)


def _retry_on_errors(retriable_types):
    def _check_error_type(error):
        return isinstance(error, retriable_types)

    return _check_error_type


class Retrier:
    DEFAULT_MAX_ATTEMPTS = 3
    DEFAULT_RETRY_ON_ERROR = _retry_on_any_error
    DEFAULT_BACKOFF = 0.5

    def __init__(self,
                 fn=None,
                 max_attempts=None,
                 retry_on_error=None,
                 retry_on_result=UNDEFINED,
                 backoff=None):
        self._fn = fn
        self._max_attempts = _validate_max_attempts(max_attempts)
        self._retry_on_error = _validate_retry_on_error(retry_on_error)
        self._retry_on_result = retry_on_result
        self._backoff = _validate_backoff(backoff)

    def invoke(self, fn=None, *args, **kwargs):
        fn = self._get_fn(fn)
        attempt = Retrier._try(fn, attempt=1, *args, **kwargs)

        while self._should_retry(attempt):
            attempt_number = attempt.attempt_number
            self._exec_backoff(attempt)
            attempt = Retrier._try(fn, attempt_number + 1, *args, **kwargs)

        return attempt.get()

    def _exec_backoff(self, attempt):
        backoff = self._backoff(attempt)
        if backoff > 0:
            time.sleep(backoff)

    def _get_fn(self, given):
        if given is not None:
            fn = given
        else:
            fn = self._fn

        if fn:
            return fn
        else:
            raise ValueError('No function/method found to be invoked')

    @staticmethod
    def _try(fn, attempt, *args, **kwargs):
        try:
            result = fn(*args, **kwargs)
            return Attempt(result, attempt, has_error=False)
        except:
            error = sys.exc_info()
            return Attempt(error, attempt, has_error=True)

    def _should_retry(self, attempt):
        if attempt.has_error:
            should_retry = self._retry_on_error(attempt.error)
        else:
            ror = self._retry_on_result
            result = attempt.result
            if ror is UNDEFINED:
                should_retry = False
            elif ror is None:
                should_retry = result is None
            elif callable(ror):
                should_retry = ror(result)
            else:
                should_retry = ror == result

        if should_retry:
            return self._max_attempts > attempt.attempt_number
        else:
            return False


class Attempt:
    def __init__(self, result, attempt_number, has_error):
        self.result = result
        self.attempt_number = attempt_number
        self.has_error = has_error

    def get(self):
        if not self.has_error:
            return self.result
        else:
            res = self.result
            six.reraise(res[0], res[1], res[2])

    @property
    def error(self):
        if self.has_error:
            return self.result[1]


def _validate_max_attempts(given):
    if given is None:
        result = Retrier.DEFAULT_MAX_ATTEMPTS
    elif isinstance(given, int) and given > 0:
        result = given
    else:
        raise ValueError(__msg_invalid_max_attempts % given)

    return result


def _validate_retry_on_error(given):
    if given is None:
        result = Retrier.DEFAULT_RETRY_ON_ERROR
    elif util.is_exception_type(given) or util.is_tuple_of_exception_types(given):
        result = _retry_on_errors(given)
    elif util.is_list_or_set_of_exception_types(given):
        result = _retry_on_errors(tuple(given))
    elif callable(given):
        result = given
    else:
        raise ValueError(__msg_invalid_retry_on_error % type(given).__name__)

    return result


def _validate_backoff(given):
    if given is None:
        result = fixed_delay(Retrier.DEFAULT_BACKOFF)
    elif util.is_number(given):
        if given == 0:
            result = no_delay
        else:
            result = fixed_delay(given)
    elif callable(given):
        result = given
    else:
        raise ValueError(__msg_invalid_backoff % type(given).__name__)

    return result


# <Backoff Functions>
def no_delay(prev_attempt): return 0


def fixed_delay(delay):
    def _get(prev_attempt): return delay

    return _get


def random_delay(minimum, maximum):
    def _get(prev_attempt):
        return random.randint(minimum, maximum)

    return _get
# </Backoff Functions>