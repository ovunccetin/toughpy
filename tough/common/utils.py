_list_or_set = (list, set)
_list_or_tuple = (list, tuple)
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


def is_list_or_tuple_of_numbers(obj):
    return isinstance(obj, _list_or_tuple) and all([is_number(x) for x in obj])


def qualified_name(fn):
    qname = []

    if hasattr(fn, '__module__'):
        module = fn.__module__
        if module: qname.append(module)

    if hasattr(fn, '__qualname__'):
        qual_name = fn.__qualname__
        if qual_name: qname.append(qual_name)

    return '.'.join(qname)


class StateError(ValueError):
    """An analogue to Java's IllegalStateException"""
    pass


__all__ = [
    'UNDEFINED',
    'is_exception_type',
    'is_tuple_of_exception_types',
    'is_list_or_set_of_exception_types',
    'is_number',
    'is_list_or_tuple_of_numbers',
    'qualified_name'
]