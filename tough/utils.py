_list_or_set = (list, set)
_numeric_types = (int, float)

UNDEFINED = object()


def is_exception_type(obj):
    return isinstance(obj, type) and issubclass(obj, BaseException)


def is_tuple_of_exception_types(obj):
    return isinstance(obj, tuple) and _are_all_exception_types(obj)


def is_list_or_set_of_exception_types(obj):
    return isinstance(obj, _list_or_set) and _are_all_exception_types(obj)


def _are_all_exception_types(obj):
    return all([is_exception_type(e) for e in obj])


def is_number(obj):
    return isinstance(obj, _numeric_types)


class StateError(ValueError):
    """An analogue to Java's IllegalStateException"""
    pass