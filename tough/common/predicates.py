from abc import abstractmethod
from .utils import *

_msg_invalid_error_predicate = '''A value of `%s` is not valid for an error predicate. It should be one of the followings:
 - Missing or None to set to the default value (i.e. retry on any error)
 - An error type, e.g. ConnectionError
 - A tuple of error types, e.g. (ConnectionError, TimeoutError)
 - A list of error types, e.g. [ConnectionError, TimeoutError]
 - A set of error types, e.g. {ConnectionError, TimeoutError}
 - A callable (e.g. a function) taking the result of the previous call and returning a boolean.
'''


class Predicate:
    def __call__(self, arg):
        return self.test(arg)

    @abstractmethod
    def test(self, arg): pass


class _Always(Predicate):
    def __init__(self, result):
        self.result = result

    def test(self, arg):
        return self.result


def __always_false(actual):
    return False


def __always_true(actual):
    return True


def never():
    return __always_false


def always():
    return __always_true


def is_instance_of(expected):
    def do_check(actual):
        return isinstance(actual, expected)

    return do_check


def is_error(expected=None):
    if expected is None:
        return is_instance_of(BaseException)
    else:
        return is_instance_of(expected)


def is_equal_to(expected):
    def do_check(actual):
        if expected is None:
            return actual is None
        else:
            return expected == actual

    return do_check


def create_error_predicate(given):
    if given is None:
        result = is_error()
    elif is_exception_type(given) or is_tuple_of_exception_types(given):
        result = is_error(given)
    elif is_list_or_set_of_exception_types(given):
        result = is_error(tuple(given))
    elif callable(given):
        result = given
    else:
        raise ValueError(_msg_invalid_error_predicate % type(given).__name__)

    return result


def create_result_predicate(given):
    if given is UNDEFINED:
        result = never()
    elif callable(given):
        result = given
    else:
        result = is_equal_to(given)

    return result
