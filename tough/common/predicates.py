from abc import abstractmethod


class _Predicate:
    @abstractmethod
    def __call__(self, arg): pass


class _IsInstanceOf(_Predicate):
    def __init__(self, expected_types):
        self.expected_types = expected_types

    def __call__(self, arg):
        if self.expected_types is None:
            return isinstance(arg, BaseException)
        else:
            return isinstance(arg, self.expected_types)


class _IsEqualTo(_Predicate):
    def __init__(self, expected_value):
        self.expected_value = expected_value

    def __call__(self, arg):
        if self.expected_value is None:
            return arg is None
        else:
            return self.expected_value == arg


class _Always(_Predicate):
    def __init__(self, result):
        self.result = result

    def __call__(self, arg):
        return self.result


class _FromCallable(_Predicate):
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, arg):
        return self.fn(arg)


__is_any_error = _IsInstanceOf(expected_types=None)
__always_true = _Always(True)
__always_false = _Always(False)


def always():
    return __always_true


def never():
    return __always_false


def is_instance_of(expected_types):
    return _IsInstanceOf(expected_types)


def is_error(expected_error_types=BaseException):
    return is_instance_of(expected_error_types)


def is_equal_to(expected_value):
    return _IsEqualTo(expected_value)


def from_callable(fn):
    return _FromCallable(fn)


def is_predicate(obj):
    return isinstance(obj, _Predicate)


__all__ = [
    'always',
    'never',
    'is_error',
    'is_equal_to',
    'from_callable'
]
