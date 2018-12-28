import sys
import time
import traceback
import six
import tough.utils as util
from .common import predicates
from .common import backoffs
from .utils import UNDEFINED

_msg_invalid_max_attempts = '`%s` is not a valid value for `max_attempts`. It should be an integer greater than 0.'

_msg_invalid_on_error = '''A value of `%s` is not valid for `on_error`. It should be one of the followings:
 - Missing or None to set to the default value (i.e. retry on any error)
 - An error type, e.g. ConnectionError
 - A tuple of error types, e.g. (ConnectionError, TimeoutError)
 - A list of error types, e.g. [ConnectionError, TimeoutError]
 - A set of error types, e.g. {ConnectionError, TimeoutError}
 - A callable (e.g. a function) taking the result of the previous call and returning a boolean.
'''

_msg_invalid_backoff = '''A value of `%s` is not valid for `backoff`. It should be on of the followings:
 - Missing or None to set the default delay.
 - A number (int or float) to put a fixed delay in seconds (e.g. 1: 1s, 1.2: 1s and 200ms).
 - A list or tuple of numbers as a sequence of delays. (e.g. [1, 2, 5]: 1s + 2s + 5s + 5s + ...)
 - A callable (e.g. a function) taking the previous Attempt object and returning a number which is the delay in seconds.
'''


class Retry:
    DEFAULT_MAX_ATTEMPTS = 3
    DEFAULT_BACKOFF = 0.5

    def __init__(self,
                 name,
                 retry_on_error=None,
                 retry_on_result=UNDEFINED,
                 max_attempts=None,
                 backoff=None,
                 max_delay=None,
                 wrap_error=False,
                 raise_if_bad_result=False):
        self._name = name
        self._max_attempts = Retry._get_max_attempts(max_attempts)
        self._error_predicate = Retry._get_error_predicate(retry_on_error)
        self._result_predicate = Retry._get_result_predicate(retry_on_result)
        self._backoff = Retry._get_backoff_fn(backoff)
        self._max_delay = max_delay
        self._wrap_error = wrap_error
        self._raise_if_bad_result = raise_if_bad_result
        self._metrics = RetryMetrics()

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
    def _get_error_predicate(given):
        if predicates.is_predicate(given):
            result = given
        elif given is None:
            result = predicates.is_error()
        elif util.is_exception_type(given) or util.is_tuple_of_exception_types(given):
            result = predicates.is_error(given)
        elif util.is_list_or_set_of_exception_types(given):
            result = predicates.is_error(tuple(given))
        elif callable(given):
            result = predicates.from_callable(given)
        else:
            raise ValueError(_msg_invalid_on_error % type(given).__name__)

        return result

    @staticmethod
    def _get_result_predicate(given):
        if predicates.is_predicate(given):
            result = given
        elif given is UNDEFINED:
            result = predicates.never()
        elif callable(given):
            result = predicates.from_callable(given)
        else:
            result = predicates.is_equal_to(given)

        return result

    @staticmethod
    def _get_backoff_fn(given):
        if given is None:
            result = backoffs.fixed(Retry.DEFAULT_BACKOFF)
        elif util.is_number(given):
            result = backoffs.fixed(given)
        elif util.is_list_or_tuple_of_numbers(given):
            result = backoffs.fixed_list(given)
        elif callable(given):
            result = given
        else:
            raise ValueError(_msg_invalid_backoff % type(given).__name__)

        return result

    @property
    def name(self):
        return self._name

    @property
    def metrics(self):
        return self._metrics

    def __call__(self, fn):
        @six.wraps(fn)
        def decorator(*args, **kwargs):
            return self.execute(fn, *args, **kwargs)

        return decorator

    # noinspection PyProtectedMember
    def execute(self, fn, *args, **kwargs):
        attempt = Retry._try(fn, 1, *args, **kwargs)

        while self._should_retry(attempt):
            self._metrics.total_retry_attempts += 1
            attempt_number = attempt.attempt_number
            self._exec_backoff(attempt_number)
            attempt = Retry._try(fn, attempt_number + 1, *args, **kwargs)

        result = attempt.result
        self._metrics.total_calls += 1

        if not attempt.has_error:  # success
            should_raise_error = self._raise_if_bad_result and self._result_predicate(result)

            if should_raise_error:
                self._metrics._increment_failed_calls(attempt)
            else:
                self._metrics._increment_successful_calls(attempt)

            if should_raise_error:
                raise RetryError(self._name, attempt)
            else:
                return result
        else:  # failure
            self._metrics._increment_failed_calls(attempt)

            if self._wrap_error:
                raise RetryError(self._name, attempt)
            else:
                six.reraise(result[0], result[1], result[2])

    @staticmethod
    def _try(fn, attempt_no, *args, **kwargs):
        try:
            return Attempt(fn(*args, **kwargs), attempt_no, has_error=False)
        except BaseException:
            error = sys.exc_info()
            return Attempt(error, attempt_no, has_error=True)

    def _should_retry(self, attempt):
        if attempt.has_error:
            should_retry = self._error_predicate(attempt.get_error())
        else:
            should_retry = self._result_predicate(attempt.result)

        if should_retry:
            return self._max_attempts > attempt.attempt_number
        else:
            return False

    def _exec_backoff(self, attempt_number):
        delay = self._backoff(attempt_no=attempt_number)
        max_delay = self._max_delay

        if max_delay and delay > max_delay:
            delay = max_delay

        if delay > 0:
            time.sleep(delay)

    def _increment_metrics_by_attempt(self, attempt):
        if attempt.has_error:
            if attempt.attempt_number == 1:
                self._metrics.failed_calls_without_retry += 1
            else:
                self._metrics.failed_calls_with_retry += 1
        else:
            if attempt.attempt_number == 1:
                self._metrics.successful_calls_without_retry += 1
            else:
                self._metrics.successful_calls_with_retry += 1


class Attempt:
    def __init__(self, result, attempt_number, has_error):
        self.result = result
        self.attempt_number = attempt_number
        self.has_error = has_error

    def get_error(self):
        if self.has_error:
            return self.result[1]

    def is_first_attempt(self):
        return self.attempt_number == 1

    def __repr__(self):
        if self.has_error:
            e_type = self.result[0]
            e_trace = self.result[2]
            return '{0}: {1}\n{2}'.format(e_type.__name__,
                                          str(self.get_error()),
                                          "".join(traceback.format_tb(e_trace)))
        else:
            return str(self.result)


class RetryError(Exception):

    def __init__(self, retry_name, last_attempt):
        self.retry_name = retry_name
        self.last_attempt = last_attempt

    def __str__(self):
        if self.last_attempt.has_error:
            return 'Retry `{0}` failed after {1} attempts! The last failure:\n{2}'.format(
                self.retry_name,
                self.last_attempt.attempt_number,
                self.last_attempt
            )
        else:
            return 'Retry `{0}` failed after {1} attempts! The last result: {2}'.format(
                self.retry_name,
                self.last_attempt.attempt_number,
                self.last_attempt
            )


class RetryMetrics:
    def __init__(self):
        self.successful_calls_without_retry = 0
        self.successful_calls_with_retry = 0
        self.failed_calls_without_retry = 0
        self.failed_calls_with_retry = 0
        self.total_calls = 0
        self.total_retry_attempts = 0

    @property
    def retry_attempts_per_call(self):
        return float(self.total_retry_attempts) / self.total_calls

    @property
    def ratio_of_successful_calls_without_retry(self):
        return self._ratio_of(self.successful_calls_without_retry)

    @property
    def ratio_of_successful_calls_with_retry(self):
        return self._ratio_of(self.successful_calls_with_retry)

    @property
    def ratio_of_failed_calls_without_retry(self):
        return self._ratio_of(self.failed_calls_without_retry)

    @property
    def ratio_of_failed_calls_with_retry(self):
        return self._ratio_of(self.failed_calls_with_retry)

    def _ratio_of(self, value):
        return float(value) / self.total_calls

    def _increment_successful_calls(self, attempt):
        if attempt.is_first_attempt():
            self.successful_calls_without_retry += 1
        else:
            self.successful_calls_with_retry += 1

    def _increment_failed_calls(self, attempt):
        if attempt.is_first_attempt():
            self.failed_calls_without_retry += 1
        else:
            self.failed_calls_with_retry += 1


def retry(func=None, name=None, retry_on_error=None, retry_on_result=UNDEFINED, max_attempts=None,
          backoff=None, max_delay=None, wrap_error=False, raise_if_bad_result=False):
    def decorate(fn):
        if name is None:
            retry_name = util.qualified_name(fn)
        else:
            retry_name = name

        retry_instance = Retry(retry_name, retry_on_error, retry_on_result, max_attempts,
                               backoff, max_delay, wrap_error, raise_if_bad_result)

        @six.wraps(fn)
        def decorator(*args, **kwargs):
            return retry_instance.execute(fn, *args, **kwargs)

        return decorator

    if callable(func):
        return decorate(func)

    return decorate


__all__ = [
    'Retry',
    'RetryError',
    'RetryMetrics',
    'retry'
]
