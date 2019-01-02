import pytest

from tough.common.attempt import *


def test_successful_attempt():
    attempt = Attempt.try_first(lambda x, y: x * y, 3, 5)

    assert isinstance(attempt, Success)
    assert attempt.is_success() is True
    assert attempt.is_failure() is False
    assert 1 == attempt.attempt_number
    assert 15 == attempt.get()
    assert attempt.get_error() is None


def test_failed_attempt():
    attempt = Attempt.try_first(lambda: 1 / 0)

    assert isinstance(attempt, Failure)
    assert attempt.is_success() is False
    assert attempt.is_failure() is True
    assert 1 == attempt.attempt_number
    assert isinstance(attempt.get_error(), ZeroDivisionError)

    with pytest.raises(ZeroDivisionError):
        attempt.get()


def test_try_next():
    attempt_1 = Attempt.try_first(lambda: 1)
    assert 1 == attempt_1.attempt_number

    attempt_2 = attempt_1.try_next(lambda: 1)
    assert 2 == attempt_2.attempt_number

    attempt_3 = attempt_2.try_next(lambda: 1)
    assert 3 == attempt_3.attempt_number
