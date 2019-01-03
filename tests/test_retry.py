import contextlib as clib

import pytest

import tough
from tests.testutil import silence, assert_close_to, Timer, timeit
from tough import retry, backoffs, RetryError
from tough.common.utils import UNDEFINED

DEFAULT_MAX_ATTEMPTS = tough.Retry.DEFAULT_MAX_ATTEMPTS
DEFAULT_BACKOFF = tough.backoffs.DEFAULT_FIXED_DELAY
DEFAULT_ELAPSED_TIME = DEFAULT_BACKOFF * (DEFAULT_MAX_ATTEMPTS - 1)


# noinspection PyPep8Naming
def Retry(on_error=None,
          on_result=UNDEFINED,
          max_attempts=DEFAULT_MAX_ATTEMPTS,
          backoff=UNDEFINED,
          max_delay=None,
          wrap_error=False,
          raise_if_bad_result=None):
    if backoff is UNDEFINED:
        backoff = 0

    return tough.Retry(on_error, on_result, max_attempts,
                       backoff, max_delay, wrap_error, raise_if_bad_result)


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class BaseRetryTest:
    def setup_method(self, method):
        self.invocations = 0

    def count_invocations(self):
        self.invocations += 1

    @clib.contextmanager
    def no_invocations(self):
        self.reset_invocations()
        yield

    def reset_invocations(self):
        self.invocations = 0

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

    def returning(self, value):
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
        with silence():
            Retry().execute(self.fail)

        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_given_times_at_most(self):
        with silence():
            Retry(max_attempts=5).execute(self.fail)

        assert 5 == self.invocations

    def test_retry_one_time_at_most(self):
        with silence():
            Retry(max_attempts=1).execute(self.fail)

        assert 1 == self.invocations


class TestRetryOnError(BaseRetryTest):
    def test_not_retry_on_unmatched_errors(self):
        rt = Retry(on_error=TypeError)

        with silence():
            rt.execute(self.fail_with(ValueError))

        assert 1 == self.invocations

    def test_retry_on_any_error_type_by_default(self):
        rt = Retry()

        with silence():
            rt.execute(self.fail_with(ValueError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with silence(), self.no_invocations():
            rt.execute(self.fail_with(TypeError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with silence(), self.no_invocations():
            rt.execute(self.fail_with(ConnectionError))
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_on_single_error_type(self):
        rt = Retry(on_error=ValueError)

        with silence():
            rt.execute(self.fail_with(ValueError))

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
        rt = Retry(on_error=lambda e: isinstance(e, ValueError))

        with silence():
            rt.execute(self.fail_with(ValueError))

        assert DEFAULT_MAX_ATTEMPTS == self.invocations


class TestRetryOnResult(BaseRetryTest):
    def test_not_retry_if_predicate_undefined(self):
        assert Retry().execute(self.returning(3)) is 3
        assert 1 == self.invocations

    def test_retry_if_result_is_none(self):
        rt = Retry(on_result=None)

        assert rt.execute(self.returning(None)) is None
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_if_result_is_undesired(self):
        rt = Retry(on_result=3)

        assert rt.execute(self.returning(3)) is 3
        assert DEFAULT_MAX_ATTEMPTS == self.invocations

    def test_retry_if_result_matches_given_predicate(self):
        rt = Retry(on_result=lambda x: x > 5)

        assert rt.execute(self.returning(6)) is 6
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

    def test_fixed_list_delay(self):
        time_elapsed = self.exec_and_timeit(Retry(backoff=(0.1, 0.2), max_attempts=4))
        assert_close_to(time_elapsed, expected=0.1 + 0.2 + 0.2)

    def test_random_delay(self):
        rt = Retry(backoff=backoffs.random(0.2, 0.3))
        time_elapsed = self.exec_and_timeit(rt)

        assert_close_to(time_elapsed, expected=0.2 * 2, delta=0.2)

    def test_linear_delay(self):
        rt = Retry(max_attempts=4, backoff=backoffs.linear(initial=0.1, accrual=0.2))
        time_elapsed = self.exec_and_timeit(rt)

        assert_close_to(time_elapsed, expected=0.1 + 0.3 + 0.5)

    def test_linear_delay_with_random_addition(self):
        rt = Retry(max_attempts=4, backoff=backoffs.linear(initial=0.1, accrual=0.2, randomizer=(0.01, 0.02)))
        time_elapsed = self.exec_and_timeit(rt)

        assert_close_to(time_elapsed, expected=0.1 + 0.3 + 0.5 + 3 * 0.01)

    def test_exponential_delay(self):
        rt = Retry(max_attempts=5, backoff=backoffs.exponential(initial=0.05))
        time_elapsed = self.exec_and_timeit(rt)

        assert_close_to(time_elapsed, expected=0.05 + 0.1 + 0.2 + 0.4)

    def test_exponential_delay_with_base(self):
        rt = Retry(max_attempts=5, backoff=backoffs.exponential(initial=0.01, base=3))
        time_elapsed = self.exec_and_timeit(rt)

        assert_close_to(time_elapsed, expected=0.01 + 0.03 + 0.09 + 0.25)

    def test_exponential_delay_with_random_addition(self):
        rt = Retry(max_attempts=5, backoff=backoffs.exponential(initial=0.05, randomizer=(0.01, 0.02)))
        time_elapsed = self.exec_and_timeit(rt)

        assert_close_to(time_elapsed, expected=0.05 + 0.1 + 0.2 + 0.4 + 4 * 0.01)

    def exec_and_timeit(self, rt):
        return timeit(lambda: rt.execute(self.fail))


class TestExecutionResult(BaseRetryTest):
    def test_returning_result(self):
        assert Retry().execute(self.returning('ok')) == 'ok'

    def test_raising_original_error(self):
        with pytest.raises(ConnectionError):
            Retry().execute(self.fail_with(ConnectionError))

    def test_raising_wrapped_error(self):
        with pytest.raises(tough.RetryError):
            Retry(wrap_error=True).execute(self.fail_with(ConnectionError))

    def test_returning_bad_result(self):
        assert Retry(on_result=0).execute(self.returning(0)) == 0

    def test_raising_error_on_bad_result(self):
        with pytest.raises(tough.RetryError):
            Retry(raise_if_bad_result=True, on_result=0).execute(self.returning(0))


class TestRetryMetrics(BaseRetryTest):
    def test_if_succeeded_at_the_first_attempt(self):
        rt = Retry()
        for _ in range(10):
            rt.execute(self.returning('ok'))

        metrics = rt.metrics
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
        rt = Retry(on_error=ConnectionError, max_attempts=4)

        for _ in range(10):
            with silence(), self.no_invocations():
                rt.execute(self.succeed_eventually(after=ConnectionError, succeed_at=3))

        metrics = rt.metrics
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
        rt = Retry(on_error=ValueError)

        for _ in range(10):
            with silence():
                rt.execute(self.fail_with(ConnectionError))

        metrics = rt.metrics
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
        rt = Retry(on_error=ConnectionError, max_attempts=3)

        for i in range(10):
            with silence():
                rt.execute(self.fail_with(ConnectionError))

        metrics = rt.metrics
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
        rt = Retry(on_result=None, max_attempts=3, raise_if_bad_result=True)

        for i in range(10):
            with silence():
                rt.execute(self.returning(None))

        metrics = rt.metrics
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
        rt = Retry(max_attempts=3, on_error=ConnectionError, on_result=None, raise_if_bad_result=True)

        for i in range(3):  # succeeds without any retry attempts
            rt.execute(self.returning('ok'))

        for i in range(5):  # succeeds at the 2nd attempt (i.e. after 1 retry)
            with silence(), self.no_invocations():
                rt.execute(self.succeed_eventually(after=ConnectionError, succeed_at=2))

        for i in range(2):  # fails without any retry attempts
            with silence():
                rt.execute(self.fail_with(ValueError))

        for i in range(4):  # fails after all retry attempts
            with silence():
                rt.execute(self.fail_with(ConnectionError))

        for i in range(2):  # fails after all retry attempts
            with silence():
                rt.execute(self.returning(None))

        metrics = rt.metrics
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


class TestDecoratorFunction(BaseRetryTest):
    def test_with_defaults(self):
        @retry
        def func1(): self.fail()

        @retry()
        def func2(): self.fail()

        with self.no_invocations():
            with pytest.raises(Exception):
                func1()
            assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with self.no_invocations():
            with pytest.raises(Exception):
                func2()
            assert DEFAULT_MAX_ATTEMPTS == self.invocations

        assert 'func1' == func1.__name__

    def test_decorated_func_with_args(self):
        @retry(on_error=OSError, backoff=0)
        def raise_given_error(err): self.fail(err)

        @retry
        def return_params_string_1(*args, **kwargs):
            return self.returning('ARGS={0}; KWARGS={1}'.format(args, kwargs))()

        @retry()
        def return_params_string_2(*args, **kwargs):
            return self.returning('ARGS={0}; KWARGS={1}'.format(args, kwargs))()

        with self.no_invocations():
            with pytest.raises(OSError):
                raise_given_error(OSError)
            assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with self.no_invocations():
            assert return_params_string_1(1, 2, 3, x=4, y=5) == "ARGS=(1, 2, 3); KWARGS={'x': 4, 'y': 5}"
            assert 1 == self.invocations

        with self.no_invocations():
            assert return_params_string_2(1, 2, 3, x=4, y=5) == "ARGS=(1, 2, 3); KWARGS={'x': 4, 'y': 5}"
            assert 1 == self.invocations

    def test_max_attempts(self):
        @retry(max_attempts=2)
        def fail(): self.fail()

        with pytest.raises(Exception):
            fail()
        assert 2 == self.invocations

    def test_retry_on_error(self):
        @retry(on_error=(ConnectionError, BufferError), backoff=0)
        def fail_with_broken_pipe(): self.fail(BrokenPipeError)

        @retry(on_error=ConnectionError)
        def fail_with_value_error(): self.fail(ValueError)

        with self.no_invocations():
            with pytest.raises(BrokenPipeError):
                fail_with_broken_pipe()
            assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with self.no_invocations():
            with pytest.raises(ValueError):
                fail_with_value_error()
            assert 1 == self.invocations

    def test_retry_on_result(self):
        @retry(on_result=None, backoff=0)
        def return_none(): return self.returning(None)()

        @retry(on_result=None)
        def return_some(): return self.returning('some')()

        @retry(on_result=lambda x: x < 0, backoff=0)
        def return_negative(): return self.returning(-1)()

        with self.no_invocations():
            return_none()
            assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with self.no_invocations():
            return_negative()
            assert DEFAULT_MAX_ATTEMPTS == self.invocations

        with self.no_invocations():
            return_some()
            assert 1 == self.invocations

    def test_backoff(self):
        @retry(backoff=0.2, max_attempts=2)
        def exec_with_fixed_backoff(): self.fail()

        @retry(backoff=backoffs.linear(initial=0.1, accrual=0.2))
        def exec_with_linear_backoff(): self.fail()

        with Timer() as t1:
            with silence():
                exec_with_fixed_backoff()

        with Timer() as t2:
            with silence():
                exec_with_linear_backoff()

        assert_close_to(t1.elapsed, expected=0.2)
        assert_close_to(t2.elapsed, expected=0.1 + 0.3)

    def test_max_delay(self):
        @retry(max_delay=0.1, backoff=2.0)
        def exec_with_max_delay(): self.fail()

        with Timer() as t1:
            with silence():
                exec_with_max_delay()

        assert_close_to(t1.elapsed, expected=0.1 * DEFAULT_MAX_ATTEMPTS)

    def test_wrap_error(self):
        @retry(wrap_error=False, backoff=0)
        def exec_without_wrapping_error(): self.fail(ValueError)

        @retry(wrap_error=True, backoff=0)
        def exec_with_wrapping_error(): self.fail(ValueError)

        with pytest.raises(ValueError):
            exec_without_wrapping_error()

        with pytest.raises(RetryError):
            exec_with_wrapping_error()

    def test_raise_if_bad_result(self):
        @retry(on_result=None, raise_if_bad_result=False, backoff=0)
        def exec_without_error_on_result(): self.returning(None)()

        @retry(on_result=None, raise_if_bad_result=True, backoff=0)
        def exec_with_error_on_result(): self.returning(None)()

        assert exec_without_error_on_result() is None

        with pytest.raises(RetryError):
            exec_with_error_on_result()
