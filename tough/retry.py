import time
import six
import tough.common.utils as util
from .common import predicates
from .common import backoffs
from .common.attempt import Attempt
from tough.common.utils import UNDEFINED

_msg_invalid_max_attempts = '`%s` is not a valid value for `max_attempts`. It should be an integer greater than 0.'


class Retry:
    DEFAULT_MAX_ATTEMPTS = 3
    DEFAULT_BACKOFF = 0.5

    def __init__(self,
                 on_error=None,
                 on_result=UNDEFINED,
                 max_attempts=None,
                 backoff=None,
                 max_delay=None,
                 wrap_error=False,
                 raise_if_bad_result=False):
        self._max_attempts = Retry._get_max_attempts(max_attempts)
        self._error_predicate = predicates.create_error_predicate(on_error)
        self._result_predicate = predicates.create_result_predicate(on_result)
        self._backoff = backoffs.create_backoff(backoff, Retry.DEFAULT_BACKOFF)
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
    def _get_name(fn):
        pass

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
        name = util.get_command_name(fn)
        attempt = Attempt.try_first(fn, *args, **kwargs)

        while self._should_retry(attempt):
            self._metrics.total_retry_attempts += 1
            attempt_number = attempt.attempt_number
            self._exec_backoff(attempt_number)
            attempt = attempt.try_next(fn, *args, **kwargs)

        self._metrics.total_calls += 1

        if attempt.is_success():  # success
            result = attempt.get()
            should_raise_error = self._raise_if_bad_result and self._result_predicate(result)

            if should_raise_error:
                self._metrics._increment_failed_calls(attempt)
            else:
                self._metrics._increment_successful_calls(attempt)

            if should_raise_error:
                raise RetryError(name, attempt)
            else:
                return result
        else:  # failure
            self._metrics._increment_failed_calls(attempt)

            if self._wrap_error:
                raise RetryError(name, attempt)
            else:
                attempt.get()  # raises the underlying error

    def _should_retry(self, attempt):
        if attempt.is_failure():
            should_retry = self._error_predicate(attempt.get_error())
        else:
            should_retry = self._result_predicate(attempt.get())

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
        if attempt.is_failure():
            if attempt.attempt_number == 1:
                self._metrics.failed_calls_without_retry += 1
            else:
                self._metrics.failed_calls_with_retry += 1
        else:
            if attempt.attempt_number == 1:
                self._metrics.successful_calls_without_retry += 1
            else:
                self._metrics.successful_calls_with_retry += 1


class RetryError(Exception):

    def __init__(self, retry_name, last_attempt):
        self.retry_name = retry_name
        self.last_attempt = last_attempt

    def __str__(self):
        if self.last_attempt.is_failure():
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
        if attempt.attempt_number == 1:
            self.successful_calls_without_retry += 1
        else:
            self.successful_calls_with_retry += 1

    def _increment_failed_calls(self, attempt):
        if attempt.attempt_number == 1:
            self.failed_calls_without_retry += 1
        else:
            self.failed_calls_with_retry += 1


def retry(func=None, on_error=None, on_result=UNDEFINED, max_attempts=None,
          backoff=None, max_delay=None, wrap_error=False, raise_if_bad_result=False):
    def decorate(fn):
        retry_instance = Retry(on_error, on_result, max_attempts,
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
