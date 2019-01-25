from tough import metrics, command
from tough.retry import retry
import pytest
from .testutil import silence


# noinspection PyTypeChecker
class TestRetryMetrics:
    current_attempt = 0

    @pytest.fixture(autouse=True)
    def around_each_test(self):
        metrics.retry_metrics.clear()
        yield

    @retry(on_result='FAILURE', on_error=TimeoutError, max_attempts=5, backoff=0)
    @command('test_command')
    def do_something(self, result=TimeoutError, succeed_at=0):
        self.current_attempt += 1
        if self.current_attempt == succeed_at:
            return result
        elif issubclass(result, Exception):
            raise result()
        else:
            return result

    def test_successful_calls_without_retry(self):
        for i in range(10):
            self.current_attempt = 0
            self.do_something(succeed_at=1)

        rm = metrics.retry_metrics['test_command']
        assert rm.successful_calls_without_retry == 10
        assert rm.successful_calls_with_retry == 0
        assert rm.failed_calls_without_retry == 0
        assert rm.failed_calls_with_retry == 0
        assert rm.total_calls == 10
        assert rm.total_retry_attempts == 0

    def test_successful_calls_with_retry(self):
        for i in range(10):
            self.current_attempt = 0
            self.do_something(succeed_at=3)

        rm = metrics.retry_metrics['test_command']
        assert rm.successful_calls_without_retry == 0
        assert rm.successful_calls_with_retry == 10
        assert rm.failed_calls_without_retry == 0
        assert rm.failed_calls_with_retry == 0
        assert rm.total_calls == 10
        assert rm.total_retry_attempts == 20

    def test_failed_calls_without_retry(self):
        for i in range(10):
            self.current_attempt = 0
            with silence():
                self.do_something(result=ConnectionError)  # ConnectionErrors not retried

        rm = metrics.retry_metrics['test_command']
        assert rm.successful_calls_without_retry == 0
        assert rm.successful_calls_with_retry == 0
        assert rm.failed_calls_without_retry == 10
        assert rm.failed_calls_with_retry == 0
        assert rm.total_calls == 10
        assert rm.total_retry_attempts == 0

    def test_failed_calls_with_retry(self):
        for i in range(10):
            self.current_attempt = 0
            with silence():
                self.do_something(result=TimeoutError)  # TimeoutErrors are retried

        rm = metrics.retry_metrics['test_command']
        assert rm.successful_calls_without_retry == 0
        assert rm.successful_calls_with_retry == 0
        assert rm.failed_calls_without_retry == 0
        assert rm.failed_calls_with_retry == 10
        assert rm.total_calls == 10
        assert rm.total_retry_attempts == 40
