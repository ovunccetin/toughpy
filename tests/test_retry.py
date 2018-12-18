import tough as tp
import pytest
import contextlib as clib
from tough.utils import UNDEFINED
from tests.testutil import silence, timeit, assert_close_to

DEFAULT_MAX_ATTEMPTS = tp.Retry.DEFAULT_MAX_ATTEMPTS
DEFAULT_BACKOFF = tp.Retry.DEFAULT_BACKOFF


# noinspection PyPep8Naming
def Retry(name='test_retry',
          max_attempts=DEFAULT_MAX_ATTEMPTS,
          on_error=None,
          on_result=UNDEFINED,
          backoff=UNDEFINED,
          max_delay=None,
          wrap_error=False,
          error_on_result=None):
    if backoff is UNDEFINED:
        backoff = 0

    return tp.Retry(name, max_attempts, on_error, on_result,
                    backoff, max_delay, wrap_error, error_on_result)


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

    def succeed_eventually(self, after, succeed_at):
        def _attempt():
            current_attempt = self.invocations + 1
            if current_attempt >= succeed_at:
                self.invocations += 1
                return 'ok'
            else:
                self.fail(after)

        return _attempt

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
        retry = Retry(on_error=TypeError)

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
        retry = Retry(on_error=ValueError)

        with silence(): retry.execute(self.fail_with(ValueError))

        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_on_collection_of_error_types(self):
        retry1 = Retry(on_error=(TypeError, ValueError))  # tuple
        retry2 = Retry(on_error=[TypeError, ValueError])  # list
        retry3 = Retry(on_error={TypeError, ValueError})  # set

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
        retry = Retry(on_error=lambda e: isinstance(e, ValueError))

        with silence(): retry.execute(self.fail_with(ValueError))

        assert DEFAULT_MAX_ATTEMPTS == self.invocations


class TestRetryOnResult(BaseRetryTest):
    def test_not_retry_if_predicate_undefined(self):
        assert Retry().execute(self.return_(3)) is 3
        assert 1 == self.invocations

    def test_retry_if_result_is_none(self):
        retry = Retry(on_result=None)

        assert retry.execute(self.return_(None)) is None
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_if_result_is_undesired(self):
        retry = Retry(on_result=3)

        assert retry.execute(self.return_(3)) is 3
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_if_result_matches_given_predicate(self):
        retry = Retry(on_result=lambda x: x > 5)

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
        retry = Retry(backoff=tp.backoff.random(0.2, 0.3))
        time_elapsed = self.exec_and_timeit(retry)

        assert_close_to(time_elapsed, expected=0.2 * 2, delta=0.2)

    def test_linear_delay(self):
        retry = Retry(max_attempts=4, backoff=tp.backoff.linear(initial=0.1, accrual=0.2))
        time_elapsed = self.exec_and_timeit(retry)

        assert_close_to(time_elapsed, expected=0.1 + 0.3 + 0.5)

    def test_linear_delay_with_random_addition(self):
        retry = Retry(max_attempts=4, backoff=tp.backoff.linear(initial=0.1, accrual=0.2, rnd=(0.01, 0.02)))
        time_elapsed = self.exec_and_timeit(retry)

        assert_close_to(time_elapsed, expected=0.1 + 0.3 + 0.5 + 3 * 0.01)

    def test_exponential_delay(self):
        retry = Retry(max_attempts=5, backoff=tp.backoff.exponential(initial=0.05))
        time_elapsed = self.exec_and_timeit(retry)

        assert_close_to(time_elapsed, expected=0.05 + 0.1 + 0.2 + 0.4)

    def test_exponential_delay_with_base(self):
        retry = Retry(max_attempts=5, backoff=tp.backoff.exponential(initial=0.01, exp_base=3))
        time_elapsed = self.exec_and_timeit(retry)

        assert_close_to(time_elapsed, expected=0.01 + 0.03 + 0.09 + 0.25)

    def test_exponential_delay_with_random_addition(self):
        retry = Retry(max_attempts=5, backoff=tp.backoff.exponential(initial=0.05, rnd=(0.01, 0.02)))
        time_elapsed = self.exec_and_timeit(retry)

        assert_close_to(time_elapsed, expected=0.05 + 0.1 + 0.2 + 0.4 + 4 * 0.01)

    def exec_and_timeit(self, retry):
        return timeit(lambda: retry.execute(self.fail))


class TestExecutionResult(BaseRetryTest):
    def test_returning_result(self):
        assert Retry().execute(self.return_('ok')) == 'ok'

    def test_raising_original_error(self):
        with pytest.raises(ConnectionError):
            Retry().execute(self.fail_with(ConnectionError))

    def test_raising_wrapped_error(self):
        with pytest.raises(tp.RetryError):
            Retry(wrap_error=True).execute(self.fail_with(ConnectionError))

    def test_returning_bad_result(self):
        assert Retry(on_result=0).execute(self.return_(0)) == 0

    def test_raising_error_on_bad_result(self):
        with pytest.raises(tp.RetryError):
            Retry(error_on_result=True, on_result=0).execute(self.return_(0))


class TestRetryMetrics(BaseRetryTest):
    def test_if_succeeded_at_the_first_attempt(self):
        retry = Retry()
        for i in range(10): retry.execute(self.return_('ok'))

        metrics = retry.metrics
        assert metrics.total_calls == 10
        assert metrics.total_retry_attempts == 0
        assert metrics.retry_attempts_per_call == 0.0

        assert metrics.successful_calls_without_retry == 10
        assert metrics.ratio_of_successful_calls_without_retry == 1.0

        assert metrics.successful_calls_with_retry == 0
        assert metrics.ratio_of_successful_calls_with_retry == 0.0

        assert metrics.failed_calls_without_retry == 0
        assert metrics.ratio_of_failed_calls_without_retry == 0.0

        assert metrics.failed_calls_with_retry == 0
        assert metrics.ratio_of_failed_calls_with_retry == 0.0

    def test_if_succeeded_after_some_retry_attempts(self):
        retry = Retry(on_error=ConnectionError, max_attempts=4)

        for i in range(10):
            with silence(), self.no_invocations():
                retry.execute(self.succeed_eventually(after=ConnectionError, succeed_at=3))

        metrics = retry.metrics
        assert metrics.total_calls == 10
        assert metrics.total_retry_attempts == 20
        assert metrics.retry_attempts_per_call == 2.0

        assert metrics.successful_calls_without_retry == 0
        assert metrics.ratio_of_successful_calls_without_retry == 0.0

        assert metrics.successful_calls_with_retry == 10
        assert metrics.ratio_of_successful_calls_with_retry == 1.0

        assert metrics.failed_calls_without_retry == 0
        assert metrics.ratio_of_failed_calls_without_retry == 0.0

        assert metrics.failed_calls_with_retry == 0
        assert metrics.ratio_of_failed_calls_with_retry == 0.0

    def test_if_failed_at_the_first_attempt(self):
        retry = Retry(on_error=ValueError)

        for i in range(10):
            with silence(): retry.execute(self.fail_with(ConnectionError))

        metrics = retry.metrics
        assert metrics.total_calls == 10
        assert metrics.total_retry_attempts == 0
        assert metrics.retry_attempts_per_call == 0.0

        assert metrics.successful_calls_without_retry == 0
        assert metrics.ratio_of_successful_calls_without_retry == 0.0

        assert metrics.successful_calls_with_retry == 0
        assert metrics.ratio_of_successful_calls_with_retry == 0.0

        assert metrics.failed_calls_without_retry == 10
        assert metrics.ratio_of_failed_calls_without_retry == 1.0

        assert metrics.failed_calls_with_retry == 0
        assert metrics.ratio_of_failed_calls_with_retry == 0.0

    def test_if_failed_after_all_retry_attempts(self):
        retry = Retry(on_error=ConnectionError, max_attempts=3)

        for i in range(10):
            with silence(): retry.execute(self.fail_with(ConnectionError))

        metrics = retry.metrics
        assert metrics.total_calls == 10
        assert metrics.total_retry_attempts == 20
        assert metrics.retry_attempts_per_call == 2.0

        assert metrics.successful_calls_without_retry == 0
        assert metrics.ratio_of_successful_calls_without_retry == 0.0

        assert metrics.successful_calls_with_retry == 0
        assert metrics.ratio_of_successful_calls_with_retry == 0.0

        assert metrics.failed_calls_without_retry == 0
        assert metrics.ratio_of_failed_calls_without_retry == 0.0

        assert metrics.failed_calls_with_retry == 10
        assert metrics.ratio_of_failed_calls_with_retry == 1.0

    def test_if_failed_due_to_invalid_result(self):
        retry = Retry(on_result=None, max_attempts=3, error_on_result=True)

        for i in range(10):
            with silence(): retry.execute(self.return_(None))

        metrics = retry.metrics
        assert metrics.total_calls == 10
        assert metrics.total_retry_attempts == 20
        assert metrics.retry_attempts_per_call == 2.0

        assert metrics.successful_calls_without_retry == 0
        assert metrics.ratio_of_successful_calls_without_retry == 0.0

        assert metrics.successful_calls_with_retry == 0
        assert metrics.ratio_of_successful_calls_with_retry == 0.0

        assert metrics.failed_calls_without_retry == 0
        assert metrics.ratio_of_failed_calls_without_retry == 0.0

        assert metrics.failed_calls_with_retry == 10
        assert metrics.ratio_of_failed_calls_with_retry == 1.0

    def test_mixed_cases(self):
        retry = Retry(max_attempts=3, on_error=ConnectionError, on_result=None, error_on_result=True)

        for i in range(3):  # succeeds without any retry attempts
            retry.execute(self.return_('ok'))

        for i in range(5):  # succeeds at the 2nd attempt (i.e. after 1 retry)
            with silence(), self.no_invocations():
                retry.execute(self.succeed_eventually(after=ConnectionError, succeed_at=2))

        for i in range(2):  # fails without any retry attempts
            with silence(): retry.execute(self.fail_with(ValueError))

        for i in range(4):  # fails after all retry attempts
            with silence(): retry.execute(self.fail_with(ConnectionError))

        for i in range(2):  # fails after all retry attempts
            with silence(): retry.execute(self.return_(None))

        metrics = retry.metrics
        assert metrics.total_calls == 16
        assert metrics.total_retry_attempts == 17
        assert metrics.retry_attempts_per_call == 1.0625

        assert metrics.successful_calls_without_retry == 3
        assert metrics.ratio_of_successful_calls_without_retry == 0.1875

        assert metrics.successful_calls_with_retry == 5
        assert metrics.ratio_of_successful_calls_with_retry == 0.3125

        assert metrics.failed_calls_without_retry == 2
        assert metrics.ratio_of_failed_calls_without_retry == 0.125

        assert metrics.failed_calls_with_retry == 6
        assert metrics.ratio_of_failed_calls_with_retry == 0.375
