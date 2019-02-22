import pytest

import toughpy.predicates as predicates
from toughpy.predicates import create_error_predicate, create_result_predicate
from toughpy.utils import UNDEFINED

an_error = BaseException('Test Error')
a_value = "test_value"


def test_always():
    assert predicates._Always().test(an_error) is True
    assert predicates._Always().test(a_value) is True
    assert predicates._Always().test(None) is True


def test_never():
    assert predicates._Never().test(an_error) is False
    assert predicates._Never().test(a_value) is False
    assert predicates._Never().test(None) is False


def test_is_instance_of():
    assert predicates._IsInstanceOf(str).test('value') is True
    assert predicates._IsInstanceOf(ValueError).test(ValueError()) is True
    assert predicates._IsInstanceOf(Exception).test(ValueError()) is True
    assert predicates._IsInstanceOf(str).test(1) is False
    assert predicates._IsInstanceOf(ValueError).test(KeyError()) is False


def test_equal_to():
    assert predicates._EqualTo(None).test(None) is True
    assert predicates._EqualTo('a').test('a') is True
    assert predicates._EqualTo(1).test(1) is True
    assert predicates._EqualTo(None).test(1) is False
    assert predicates._EqualTo('a').test('b') is False
    assert predicates._EqualTo(1).test(2) is False


def test_custom_predicate():
    predicate = predicates._CustomPredicate(lambda x: True if x == 1 else False)
    assert predicate.test(1) is True
    assert predicate.test(2) is False


def test_create_error_predicate():
    assert predicates.__IS_ANY_ERROR == create_error_predicate(None)
    assert predicates.__NEVER == create_error_predicate(UNDEFINED)
    assert predicates._IsInstanceOf(ValueError) == create_error_predicate(ValueError)
    assert predicates._IsInstanceOf((KeyError, ValueError)) == create_error_predicate([KeyError, ValueError])
    assert isinstance(create_error_predicate(lambda: False), predicates._CustomPredicate)

    with pytest.raises(ValueError):
        create_error_predicate(10)


def test_create_result_predicate():
    assert predicates.__NEVER == create_result_predicate(UNDEFINED)
    assert isinstance(create_result_predicate(lambda: False), predicates._CustomPredicate)
    assert predicates._EqualTo(5) == create_result_predicate(5)
