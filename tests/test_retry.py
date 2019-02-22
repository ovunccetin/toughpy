from toughpy.retry import *
import random as rnd
import pytest
from tests.testutil import assert_close_to, timeit
from toughpy.utils import UNDEFINED

ERROR_TYPES = [TimeoutError, ConnectionError, OSError, ValueError, KeyError, BaseException, Exception]
DEFAULT_BACKOFF = 0.5


def is_timeout_error(e):
    return isinstance(e, TimeoutError)


def is_negative(val):
    return val < 0


class BaseRetryTest:
    invocations = 0

    @pytest.fixture(autouse=True)
    def around_each_test(self):
        self.invocations = 0
        yield
        self.invocations = 0

    def fail_(self):
        return self.fail_with(rnd.choice(ERROR_TYPES))

    def fail_with(self, error_type):
        def _do():
            self.invocations += 1
            raise error_type()

        return _do

    def return_(self, value):
        def _do():
            self.invocations += 1
            return value

        return _do


class TestRetryOnError(BaseRetryTest):

    def test_never_retry(self):
        with pytest.raises(BaseException):
            retry(self.fail_(), backoff=0, on_error=UNDEFINED).__call__()

        assert 1 == self.invocations

    def test_retry_with_default_predicate(self):
        with pytest.raises(BaseException):
            retry(self.fail_(), backoff=0).__call__()

        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_if_predicate_matches_the_error(self):
        with pytest.raises(BaseException):
            retry(self.fail_with(ConnectionError), on_error=OSError, backoff=0).__call__()

        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_not_retry_if_predicate_doesnt_match_the_error(self):
        with pytest.raises(BaseException):
            retry(self.fail_with(ConnectionError), on_error=TimeoutError, backoff=0).__call__()

        assert 1 == self.invocations

    def test_with_custom_predicate(self):
        with pytest.raises(BaseException):
            retry(self.fail_with(TimeoutError), on_error=is_timeout_error, backoff=0).__call__()

        assert DEFAULT_MAX_ATTEMPTS == self.invocations


class TestRetryOnResult(BaseRetryTest):
    def test_never_retry_by_default(self):
        retry(self.return_(None), backoff=0).__call__()
        assert 1 == self.invocations

    def test_retry_if_predicate_matches_the_result(self):
        retry(self.return_(None), on_result=None, backoff=0).__call__()
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_not_retry_if_predicate_doesnt_match_the_result(self):
        retry(self.return_(2), on_result=1, backoff=0).__call__()
        assert 1 == self.invocations

    def test_with_custom_predicate(self):
        retry(self.return_(-1), on_result=is_negative, backoff=0).__call__()
        assert DEFAULT_MAX_ATTEMPTS == self.invocations


class TestMaxAttempts(BaseRetryTest):
    def test_invalid_values(self):
        with pytest.raises(ValueError):
            retry(self.fail_(), max_attempts=0)

        with pytest.raises(ValueError):
            retry(self.fail_(), max_attempts=-1)

        with pytest.raises(ValueError):
            retry(self.fail_(), max_attempts='x')

    def test_single_attempt(self):
        with pytest.raises(BaseException):
            retry(self.fail_(), max_attempts=1, backoff=0).__call__()

        assert 1 == self.invocations

    def test_retry_at_most(self):
        with pytest.raises(BaseException):
            retry(self.fail_(), max_attempts=5, backoff=0).__call__()

        assert 5 == self.invocations


class TestBackoff(BaseRetryTest):
    def test_default_value(self):
        elapsed_time = timeit(retry(self.fail_(), max_attempts=2))
        assert_close_to(elapsed_time, expected=DEFAULT_BACKOFF)

    def test_put_delays_wrt_backoff_policy(self):
        elapsed_time = timeit(retry(self.fail_(), backoff=0.1))
        assert_close_to(elapsed_time, expected=0.1 * 2)

        elapsed_time = timeit(retry(self.fail_(), backoff=[0.1, 0.2]))
        assert_close_to(elapsed_time, expected=0.1 + 0.2)


class TestOutcome(BaseRetryTest):
    def test_unwrapped_error(self):
        with pytest.raises(TimeoutError):
            retry(self.fail_with(TimeoutError), backoff=0).__call__()

    def test_wrapped_error(self):
        with pytest.raises(RetryError):
            retry(self.fail_with(TimeoutError), wrap_error=True, backoff=0).__call__()

    def test_bad_result(self):
        assert retry(self.return_(None), on_result=None, backoff=0).__call__() is None

    def test_raise_if_bad_result(self):
        with pytest.raises(RetryError):
            retry(self.return_(None), on_result=None, raise_if_bad_result=True, backoff=0).__call__()


class TestCustomDecorator(BaseRetryTest):
    def test_a_custom_fixed_decorator(self):
        custom_retry = Retry(on_result=is_negative, max_attempts=5, backoff=0)

        @custom_retry
        def return_negatives():
            return self.return_(rnd.randint(-10, -1))()

        return_negatives()

        assert 5 == self.invocations

    def test_a_parameterized_decorator(self):
        def custom_retry(max_retries):
            return Retry(on_result=None, max_attempts=max_retries + 1, backoff=0)

        @custom_retry(max_retries=3)
        def return_none():
            return self.return_(None)()

        return_none()

        assert 4 == self.invocations
