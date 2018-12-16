import toughpy.utils as util
from toughpy.utils import UNDEFINED
from toughpy.stopwatch import Stopwatch
import six
import sys
import time
import random
import traceback

_msg_invalid_max_attempts = '`%s` is not a valid value for `max_attempts`. It should be an integer greater than 0.'

_msg_invalid_retry_on_error = '''A value of `%s` is not valid for `retry_on_error`. It should be one of the followings:
 - Missing or None to set to the default value (i.e. retry on any error)
 - An error type, e.g. ConnectionError
 - A tuple of error types, e.g. (ConnectionError, TimeoutError)
 - A list of error types, e.g. [ConnectionError, TimeoutError]
 - A set of error types, e.g. {ConnectionError, TimeoutError}
 - A callable (e.g. a function) taking the result of the previous call and returning a boolean.
'''

_msg_invalid_backoff = '''A value of `%s` is not valid for `backoff`. It should be on of the followings:
 - Missing or None to set the default delay.
 - An integer to put a fixed delay in seconds (e.g. 1 means 1 second).
 - A float to put a fixed delay in seconds (e.g. 1.3 means 1 second and 300 milliseconds)
 - A callable (e.g. a function) taking the previous Attempt object and returning a number which is the delay in seconds.
'''


class Retry:
    DEFAULT_MAX_ATTEMPTS = 3
    DEFAULT_BACKOFF = 0.5

    def __init__(self,
                 name,
                 max_attempts=None,
                 retry_on_error=None,
                 retry_on_result=UNDEFINED,
                 backoff=None,
                 max_delay=None,
                 wrap_result=False):
        self._name = name
        self._max_attempts = Retry._get_max_attempts(max_attempts)
        self._retry_on_error = Retry._get_retry_on_error_fn(retry_on_error)
        self._retry_on_result = Retry._get_retry_on_result_fn(retry_on_result)
        self._backoff = Retry._get_backoff_fn(backoff)
        self._max_delay = max_delay
        self._wrap_result = wrap_result

    @staticmethod
    def _get_max_attempts(given):
        if given is None:
            result = Retry.DEFAULT_MAX_ATTEMPTS
        elif isinstance(given, int) and given > 0:
            result = given
        else:
            raise ValueError(_msg_invalid_max_attempts % given)

        return result

    @staticmethod
    def _get_retry_on_error_fn(given):
        if given is None:
            result = _predicates.on_any_error
        elif util.is_exception_type(given) or util.is_tuple_of_exception_types(given):
            result = _predicates.on_errors(given)
        elif util.is_list_or_set_of_exception_types(given):
            result = _predicates.on_errors(tuple(given))
        elif callable(given):
            result = given
        else:
            raise ValueError(_msg_invalid_retry_on_error % type(given).__name__)

        return result

    @staticmethod
    def _get_retry_on_result_fn(given):
        if given is UNDEFINED:
            result = _predicates.never
        elif callable(given):
            result = given
        else:
            result = _predicates.on_result(given)

        return result

    @staticmethod
    def _get_backoff_fn(given):
        if given is None:
            result = backoffs.fixed_delay(Retry.DEFAULT_BACKOFF)
        elif util.is_number(given):
            result = backoffs.fixed_delay(given)
        elif callable(given):
            result = given
        else:
            raise ValueError(_msg_invalid_backoff % type(given).__name__)

        return result

    @property
    def name(self):
        return self._name

    def execute(self, fn, *args, **kwargs):
        timer = Stopwatch.create_started()
        attempt = Retry._try(fn, attempt=1, *args, **kwargs)

        while self._should_retry(attempt):
            attempt_number = attempt.attempt_number
            self._exec_backoff(attempt)
            attempt = Retry._try(fn, attempt_number + 1, *args, **kwargs)

        elapsed_time = timer.stop().elapsed_time()

        if self._wrap_result:
            return RetryResult(self.name, attempt, elapsed_time)
        else:
            return attempt.get(self._name)

    def _exec_backoff(self, attempt):
        delay = self._backoff(attempt)
        max_delay = self._max_delay

        if max_delay and delay > max_delay:
            delay = max_delay

        if delay > 0:
            time.sleep(delay)

    @staticmethod
    def _try(fn, attempt, *args, **kwargs):
        try:
            result = fn(*args, **kwargs)
            return _Attempt(result, attempt, has_error=False)
        except:
            error = sys.exc_info()
            return _Attempt(error, attempt, has_error=True)

    def _should_retry(self, attempt):
        if attempt.has_error:
            should_retry = self._retry_on_error(attempt.error)
        else:
            should_retry = self._retry_on_result(attempt.result)

        if should_retry:
            return self._max_attempts > attempt.attempt_number
        else:
            return False


class _Attempt:
    def __init__(self, result, attempt_number, has_error):
        self.result = result
        self.attempt_number = attempt_number
        self.has_error = has_error

    def get(self, retry_name, wrap_error=False):
        if not self.has_error:
            return self.result
        else:
            res = self.result
            if wrap_error:
                raise RetryError(retry_name, self)
            else:
                six.reraise(res[0], res[1], res[2])

    @property
    def error(self):
        if self.has_error:
            return self.result[1]

    def __repr__(self):
        if self.has_error:
            e_type = self.result[0]
            e_trace = self.result[2]
            return '{0}: {1}\n{2}'.format(e_type.__name__, str(self.error), "".join(traceback.format_tb(e_trace)))
        else:
            return 'Result: {0}'.format(self.result)


class RetryError(Exception):

    def __init__(self, retry_name, last_attempt):
        self.retry_name = retry_name
        self.last_attempt = last_attempt

    def __str__(self):
        return 'Retry `{0}` failed after {1} attempts! The last failure:\n{2}'.format(
            self.retry_name,
            self.last_attempt.attempt_number,
            self.last_attempt
        )


class RetryResult:
    def __init__(self, name, last_attempt, elapsed_time):
        self._name = name
        self._last_attempt = last_attempt
        self._elapsed_time = elapsed_time

    def get(self, wrap_error=False):
        return self._last_attempt.get(self._name, wrap_error)

    def elapsed_time(self):
        return self._elapsed_time

    def elapsed_millis(self):
        return self.elapsed_time().to_millis()

    @property
    def failure(self):
        return self._last_attempt.has_error

    @property
    def successful(self):
        return not self._last_attempt.has_error

    @property
    def last_attempt_number(self):
        return self._last_attempt.attempt_number


# noinspection PyUnusedLocal
class _predicates:

    @staticmethod
    def on_any_error(error):
        return isinstance(error, BaseException)

    @staticmethod
    def on_errors(retriable_types):
        def _check_error_type(error):
            return isinstance(error, retriable_types)

        return _check_error_type

    @staticmethod
    def on_result(retriable):
        def _check_result(result):
            if retriable is None:
                return result is None
            else:
                return retriable == result

        return _check_result

    @staticmethod
    def never(result):
        return False


# noinspection PyUnusedLocal
class backoffs:
    @staticmethod
    def fixed_delay(delay):
        def _get(prev_attempt=None):
            return delay

        return _get

    @staticmethod
    def random_delay(min_sec, max_sec):
        def _get(prev_attempt=None):
            lb = int(min_sec * 1000)
            ub = int(max_sec * 1000)

            ms = random.randint(lb, ub)
            return float(ms) / 1000

        return _get

    @staticmethod
    def linear_delay(initial, accrual, rnd=None):
        rnd_fn = backoffs._get_rnd_fn(rnd)

        def _get(prev_attempt):
            attempt_number = backoffs._get_attempt_number(prev_attempt)

            return initial + accrual * (attempt_number - 1) + rnd_fn()

        return _get

    @staticmethod
    def exponential_delay(initial, exp_base=2, rnd=None):
        rnd_fn = backoffs._get_rnd_fn(rnd)

        def _get(prev_attempt):
            attempt_number = backoffs._get_attempt_number(prev_attempt)
            return initial * exp_base ** (attempt_number - 1) + rnd_fn()

        return _get

    @staticmethod
    def _get_rnd_fn(rnd):
        if callable(rnd):
            fn = rnd
        elif isinstance(rnd, tuple):
            fn = backoffs.random_delay(rnd[0], rnd[1])
        else:
            fn = lambda: 0

        return fn

    @staticmethod
    def _get_attempt_number(attempt):
        if isinstance(attempt, _Attempt):
            return attempt.attempt_number
        elif isinstance(attempt, int):
            return attempt
        else:
            raise ValueError('Invalid attempt: %s' % str(attempt))
