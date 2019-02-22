class RetryMetrics:
    def __init__(self, name):
        self.name = name
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


class MetricsRegistry:
    def __init__(self, metrics_type):
        self.__register = {}
        self.__metrics_type = metrics_type

    def __getitem__(self, key):
        metrics = self.__register.get(key)
        if metrics is None:
            metrics = self.__metrics_type(key)
            self.__register[key] = metrics

        return metrics

    def clear(self):
        self.__register.clear()


retry_metrics = MetricsRegistry(RetryMetrics)

__all__ = [
    'retry_metrics',
    'RetryMetrics'
]
