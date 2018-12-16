import toughpy as tp
from tests.testutil import silence, timeit, assert_close_to
import pytest
import contextlib as clib
from toughpy.utils import UNDEFINED

DEFAULT_MAX_ATTEMPTS = tp.Retry.DEFAULT_MAX_ATTEMPTS
DEFAULT_BACKOFF = tp.Retry.DEFAULT_BACKOFF


# noinspection PyPep8Naming
def Retry(name='test_retry',
          max_attempts=DEFAULT_MAX_ATTEMPTS,
          retry_on_error=None,
          retry_on_result=UNDEFINED,
          backoff=UNDEFINED,
          max_delay=None,
          wrap_result=False):
    if backoff is UNDEFINED:
        backoff = 0

    return tp.Retry(name, max_attempts, retry_on_error, retry_on_result, backoff, max_delay, wrap_result)


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
        raise error_type('Expected test failure')

    def fail_with(self, error_type):
        def _fail(): self.fail(error_type)

        return _fail

    def return_(self, value):
        def _return_():
            self.count_invocations()
            return value

        return _return_


class TestMaxAttempts(BaseRetryTest):
    def test_valid_values(self):
        Retry()
        Retry(max_attempts=5)

        with pytest.raises(ValueError):
            Retry(max_attempts=0)

        with pytest.raises(ValueError):
            Retry(max_attempts=-1)

        with pytest.raises(ValueError):
            Retry(max_attempts='1')

    def test_retry_default_times_at_most(self):
        with silence(): Retry().execute(self.fail)

        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_given_times_at_most(self):
        with silence(): Retry(max_attempts=5).execute(self.fail)

        assert 5 == self.invocations

    def test_retry_one_time_at_most(self):
        with silence(): Retry(max_attempts=1).execute(self.fail)

        assert 1 == self.invocations


class TestRetryOnError(BaseRetryTest):
    def test_not_retry_on_unmatched_errors(self):
        retry = Retry(retry_on_error=TypeError)

        with silence(): retry.execute(self.fail_with(ValueError))

        assert 1 == self.invocations

    def test_retry_on_any_error_type_by_default(self):
        retry = Retry()

        with silence():
            retry.execute(self.fail_with(ValueError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with silence(), self.no_invocations():
            retry.execute(self.fail_with(TypeError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with silence(), self.no_invocations():
            retry.execute(self.fail_with(ConnectionError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_on_single_error_type(self):
        retry = Retry(retry_on_error=ValueError)

        with silence(): retry.execute(self.fail_with(ValueError))

        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_on_collection_of_error_types(self):
        retry1 = Retry(retry_on_error=(TypeError, ValueError))  # tuple
        retry2 = Retry(retry_on_error=[TypeError, ValueError])  # list
        retry3 = Retry(retry_on_error={TypeError, ValueError})  # set

        with silence():
            retry1.execute(self.fail_with(ValueError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with silence(), self.no_invocations():
            retry2.execute(self.fail_with(ValueError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with silence(), self.no_invocations():
            retry3.execute(self.fail_with(ValueError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_wrt_a_predicate_function(self):
        retry = Retry(retry_on_error=lambda e: isinstance(e, ValueError))

        with silence(): retry.execute(self.fail_with(ValueError))

        assert DEFAULT_MAX_ATTEMPTS == self.invocations


class TestRetryOnResult(BaseRetryTest):
    def test_not_retry_if_predicate_undefined(self):
        assert Retry().execute(self.return_(3)) is 3
        assert 1 == self.invocations

    def test_retry_if_result_is_none(self):
        retry = Retry(retry_on_result=None)

        assert retry.execute(self.return_(None)) is None
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_if_result_is_undesired(self):
        retry = Retry(retry_on_result=3)

        assert retry.execute(self.return_(3)) is 3
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_if_result_matches_given_predicate(self):
        retry = Retry(retry_on_result=lambda x: x > 5)

        assert retry.execute(self.return_(6)) is 6
        assert DEFAULT_MAX_ATTEMPTS == self.invocations


class TestBackoff(BaseRetryTest):
    def test_no_backoff(self):
        time_elapsed = self.exec_and_timeit(Retry())

        assert_close_to(time_elapsed, expected=0)

    def test_default_backoff(self):
        time_elapsed = self.exec_and_timeit(Retry(backoff=DEFAULT_BACKOFF))

        assert_close_to(time_elapsed, expected=DEFAULT_BACKOFF * 2)

    def test_fixed_delay(self):
        time_elapsed = self.exec_and_timeit(Retry(backoff=0.25))

        assert_close_to(time_elapsed, expected=0.25 * 2)

    def test_random_delay(self):
        retry = Retry(backoff=tp.random_delay(0.2, 0.3))
        time_elapsed = self.exec_and_timeit(retry)

        assert_close_to(time_elapsed, expected=0.2 * 2, delta=0.2)

    def test_linear_delay(self):
        retry = Retry(max_attempts=4, backoff=tp.linear_delay(initial=0.1, accrual=0.2))
        time_elapsed = self.exec_and_timeit(retry)

        assert_close_to(time_elapsed, expected=0.1 + 0.3 + 0.5)

    def test_linear_delay_with_random_addition(self):
        retry = Retry(max_attempts=4, backoff=tp.linear_delay(initial=0.1, accrual=0.2, rnd=(0.01, 0.02)))
        time_elapsed = self.exec_and_timeit(retry)

        assert_close_to(time_elapsed, expected=0.1 + 0.3 + 0.5 + 3 * 0.01)

    def test_exponential_delay(self):
        retry = Retry(max_attempts=5, backoff=tp.exponential_delay(initial=0.05))
        time_elapsed = self.exec_and_timeit(retry)

        assert_close_to(time_elapsed, expected=0.05 + 0.1 + 0.2 + 0.4)

    def test_exponential_delay_with_base(self):
        retry = Retry(max_attempts=5, backoff=tp.exponential_delay(initial=0.01, exp_base=3))
        time_elapsed = self.exec_and_timeit(retry)

        assert_close_to(time_elapsed, expected=0.01 + 0.03 + 0.09 + 0.25)

    def test_exponential_delay_with_random_addition(self):
        retry = Retry(max_attempts=5, backoff=tp.exponential_delay(initial=0.05, rnd=(0.01, 0.02)))
        time_elapsed = self.exec_and_timeit(retry)

        assert_close_to(time_elapsed, expected=0.05 + 0.1 + 0.2 + 0.4 + 4 * 0.01)

    def exec_and_timeit(self, retry):
        return timeit(lambda: retry.execute(self.fail))


class TestExecutionResult(BaseRetryTest):
    def test_unwrapped_result(self):
        assert Retry().execute(self.return_('ok')) == 'ok'

    def test_unwrapped_error(self):
        with pytest.raises(ConnectionError):
            Retry().execute(self.fail_with(ConnectionError))

    def test_wrapped_result(self):
        result = Retry(wrap_result=True).execute(self.return_('ok'))

        assert result.is_success is True
        assert result.is_failure is False
        assert 'ok' == result.get()
        assert 1 == result.last_attempt_number
        assert_close_to(result.elapsed_time.to_millis(), expected=0)

    def test_wrapped_error(self):
        retry = Retry(wrap_result=True, max_attempts=3, backoff=0.1)
        result = retry.execute(self.fail_with(ConnectionError))

        assert result.is_success is False
        assert result.is_failure is True
        assert 3 == result.last_attempt_number
        assert_close_to(result.elapsed_time.to_millis(), expected=200, delta=100)

        with pytest.raises(ConnectionError):
            result.get()

        with pytest.raises(tp.RetryError):
            result.get(wrap_error=True)
