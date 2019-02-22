from abc import abstractmethod
from toughpy.utils import *

_msg_invalid_error_predicate = '''A value of `%s` is not valid for an error predicate. It should be one of the followings:
 - None to set to the default predicate (i.e. retry on any error type)
 - An error type, e.g. ConnectionError.
 - A tuple of error types, e.g. (ConnectionError, TimeoutError).
 - A list of error types, e.g. [ConnectionError, TimeoutError].
 - A set of error types, e.g. {ConnectionError, TimeoutError}.
 - A callable taking an argument and returning a boolean.
'''


class Predicate:
    def __call__(self, arg):
        return self.test(arg)

    @abstractmethod
    def test(self, arg): pass


class _Always(Predicate):
    def test(self, arg):
        return True


class _Never(Predicate):
    def test(self, arg):
        return False


class _IsInstanceOf(Predicate):

    def __init__(self, expected_type):
        self.expected_type = expected_type

    def test(self, arg):
        return isinstance(arg, self.expected_type)

    def __eq__(self, other):
        if isinstance(other, _IsInstanceOf):
            return self.expected_type == other.expected_type
        else:
            return False


class _EqualTo(Predicate):
    def __init__(self, expected_value):
        self.expected_value = expected_value

    def test(self, arg):
        if self.expected_value is None:
            return arg is None
        else:
            return self.expected_value == arg

    def __eq__(self, other):
        if isinstance(other, _EqualTo):
            return self.expected_value == other.expected_value
        else:
            return False


class _CustomPredicate(Predicate):
    def __init__(self, func):
        self._func = func

    def test(self, arg):
        return self._func.__call__(arg)


__IS_ANY_ERROR = _IsInstanceOf(BaseException)
__NEVER = _Never()
__ALWAYS = _Always()


def create_error_predicate(hint):
    if isinstance(hint, Predicate):
        result = hint
    elif hint is None:
        result = __IS_ANY_ERROR
    elif hint is UNDEFINED:
        result = __NEVER
    elif is_exception_type(hint) or is_tuple_of_exception_types(hint):
        result = _IsInstanceOf(hint)
    elif is_list_or_set_of_exception_types(hint):
        result = _IsInstanceOf(tuple(hint))
    elif callable(hint):
        result = _CustomPredicate(hint)
    else:
        raise ValueError(_msg_invalid_error_predicate % type(hint).__name__)

    return result


def create_result_predicate(hint):
    if hint is UNDEFINED:
        result = __NEVER
    elif callable(hint):
        result = _CustomPredicate(hint)
    else:
        result = _EqualTo(hint)

    return result
