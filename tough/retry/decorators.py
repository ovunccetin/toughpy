import six
from tough.utils import UNDEFINED
from .policy import RetryPolicy


class Retry:
    error_predicate = None
    result_predicate = UNDEFINED
    max_attempts = None
    backoff = None
    max_delay = None
    wrap_error = False
    raise_if_bad_result = False

    def __init__(self, func):
        self._func = func
        self._policy = self._create_policy()

    def _create_policy(self):
        return RetryPolicy(on_error=self.error_predicate,
                           on_result=self.result_predicate,
                           max_attempts=self.max_attempts,
                           backoff=self.backoff,
                           wrap_error=self.wrap_error,
                           raise_if_bad_result=self.raise_if_bad_result)

    def __call__(self, *args, **kwargs):
        self._policy.execute(self._func, *args, *kwargs)


def retry(func=None, on_error=None, on_result=UNDEFINED, max_attempts=None,
          backoff=None, max_delay=None, wrap_error=False, raise_if_bad_result=False):
    def decorate(fn):
        policy = RetryPolicy(on_error, on_result, max_attempts,
                             backoff, max_delay, wrap_error, raise_if_bad_result)

        @six.wraps(fn)
        def decorator(*args, **kwargs):
            return policy.execute(fn, *args, **kwargs)

        return decorator

    if callable(func):
        return decorate(func)

    return decorate


__all__ = [
    'Retry',
    'retry'
]
