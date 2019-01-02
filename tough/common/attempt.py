from abc import abstractmethod
import sys
import six
import traceback


class Attempt:
    @classmethod
    def try_first(cls, fn, *args, **kwargs):
        return cls(0).try_next(fn, *args, **kwargs)

    def __init__(self, attempt_number):
        self._attempt_number = attempt_number

    @property
    def attempt_number(self):
        return self._attempt_number

    @abstractmethod
    def is_success(self):
        pass

    def is_failure(self):
        return not self.is_success()

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def get_error(self):
        pass

    def try_next(self, fn, *args, **kwargs):
        next_attempt_number = self.attempt_number + 1
        try:
            return Success(fn(*args, **kwargs), next_attempt_number)
        except BaseException:
            return Failure(sys.exc_info(), next_attempt_number)


class Success(Attempt):
    def __init__(self, value, attempt_number=1):
        super().__init__(attempt_number)
        self._value = value

    def is_success(self):
        return True

    def get(self):
        return self._value

    def get_error(self):
        return None

    def __repr__(self):
        return str(self._value)


class Failure(Attempt):
    def __init__(self, exc_info, attempt_number=1):
        super().__init__(attempt_number)
        self._error_type = exc_info[0]
        self._error = exc_info[1]
        self._traceback = exc_info[2]

    def is_success(self):
        return False

    def get(self):
        six.reraise(self._error_type, self._error, self._traceback)

    def get_error(self):
        return self._error

    def __repr__(self) -> str:
        return '{0}: {1}\n{2}'.format(self._error_type.__name__,
                                      str(self.get_error()),
                                      "".join(traceback.format_tb(self._traceback)))


__all__ = [
    'Attempt',
    'Success',
    'Failure'
]
