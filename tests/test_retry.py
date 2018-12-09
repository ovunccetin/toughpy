import toughpy as tp
from tests.testutil import silence, timeit
import pytest
import contextlib as clib

DEFAULT_MAX_ATTEMPTS = tp.Retrier.DEFAULT_MAX_ATTEMPTS
DEFAULT_BACKOFF = tp.Retrier.DEFAULT_BACKOFF


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class BaseRetryTest:
    def setup_method(self, method):
        self.invocations = 0

    def count_invocations(self):
        self.invocations += 1

    @clib.contextmanager
    def no_invocations(self):
        self.invocations = 0
        yield

    def fail(self, error_type=Exception):
        self.count_invocations()
        raise error_type()

    def fail_with(self, error_type):
        def _fail(): self.fail(error_type)

        return _fail

    def fail_with_value_error(self):
        self.fail_with(ValueError).__call__()

    def return_(self, value):
        def _return_():
            self.count_invocations()
            return value

        return _return_


class TestMaxAttempts(BaseRetryTest):
    def test_valid_values(self):
        tp.Retrier(self.fail)
        tp.Retrier(self.fail, max_attempts=5)

        with pytest.raises(ValueError):
            tp.Retrier(self.fail, max_attempts=0)

        with pytest.raises(ValueError):
            tp.Retrier(self.fail, max_attempts=-1)

        with pytest.raises(ValueError):
            tp.Retrier(self.fail, max_attempts='1')

    def test_retry_default_times_at_most(self):
        retrier = tp.Retrier(self.fail, backoff=0)

        with silence(): retrier.invoke()

        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_given_times_at_most(self):
        retrier = tp.Retrier(self.fail, max_attempts=5, backoff=0)

        with silence(): retrier.invoke()

        assert 5 == self.invocations

    def test_retry_one_time_at_most(self):
        retrier = tp.Retrier(self.fail, max_attempts=1, backoff=0)

        with silence(): retrier.invoke()

        assert 1 == self.invocations


class TestRetryOnError(BaseRetryTest):
    def test_not_retry_on_unmatched_errors(self):
        retrier = tp.Retrier(retry_on_error=TypeError, backoff=0)

        with silence(): retrier.invoke(self.fail_with(ValueError))

        assert 1 == self.invocations

    def test_retry_on_any_error_type_by_default(self):
        retrier = tp.Retrier(backoff=0)

        with silence():
            retrier.invoke(self.fail_with(ValueError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with silence(), self.no_invocations():
            retrier.invoke(self.fail_with(TypeError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with silence(), self.no_invocations():
            retrier.invoke(self.fail_with(ConnectionError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_on_single_error_type(self):
        retrier = tp.Retrier(retry_on_error=ValueError, backoff=0)

        with silence(): retrier.invoke(self.fail_with(ValueError))

        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_on_collection_of_error_types(self):
        retrier1 = tp.Retrier(retry_on_error=(TypeError, ValueError), backoff=0)  # tuple
        retrier2 = tp.Retrier(retry_on_error=[TypeError, ValueError], backoff=0)  # list
        retrier3 = tp.Retrier(retry_on_error={TypeError, ValueError}, backoff=0)  # set

        with silence():
            retrier1.invoke(self.fail_with(ValueError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with silence(), self.no_invocations():
            retrier2.invoke(self.fail_with(ValueError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with silence(), self.no_invocations():
            retrier3.invoke(self.fail_with(ValueError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_wrt_a_predicate_function(self):
        retrier = tp.Retrier(retry_on_error=lambda e: isinstance(e, ValueError), backoff=0)

        with silence(): retrier.invoke(self.fail_with(ValueError))

        assert DEFAULT_MAX_ATTEMPTS == self.invocations


class TestRetryOnResult(BaseRetryTest):
    def test_not_retry_if_predicate_undefined(self):
        retrier = tp.Retrier(backoff=0)

        assert retrier.invoke(self.return_(3)) is 3
        assert 1 == self.invocations

    def test_retry_if_result_is_none(self):
        retrier = tp.Retrier(retry_on_result=None, backoff=0)

        assert retrier.invoke(self.return_(None)) is None
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_if_result_is_undesired(self):
        retrier = tp.Retrier(retry_on_result=3, backoff=0)

        assert retrier.invoke(self.return_(3)) is 3
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_if_result_matches_given_predicate(self):
        retrier = tp.Retrier(retry_on_result=lambda x: x > 5, backoff=0)

        assert retrier.invoke(self.return_(6)) is 6
        assert DEFAULT_MAX_ATTEMPTS == self.invocations


class TestBackoff(BaseRetryTest):
    def test_no_backoff(self):
        retrier = tp.Retrier(max_attempts=3, backoff=0)
        time_elapsed = timeit(lambda: retrier.invoke(self.fail))

        assert 0 <= time_elapsed <= DEFAULT_BACKOFF

    def test_default_backoff(self):
        retrier = tp.Retrier(max_attempts=3)
        time_elapsed = timeit(lambda: retrier.invoke(self.fail))

        assert time_elapsed >= DEFAULT_BACKOFF * 2

    def test_fixed_delay(self):
        retrier = tp.Retrier(max_attempts=3, backoff=0.25)
        time_elapsed = timeit(lambda: retrier.invoke(self.fail))

        assert time_elapsed >= 0.25 * 2

    def test_random_delay(self):
        retrier = tp.Retrier(max_attempts=2, backoff=tp.retry.random_delay(1, 2))
        time_elapsed = timeit(lambda: retrier.invoke(self.fail))

        assert time_elapsed >= 1