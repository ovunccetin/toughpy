def on_any_error(error):
    return isinstance(error, BaseException)


def on_errors(expected_types):
    def _check_error_type(error):
        return isinstance(error, expected_types)

    return _check_error_type


def on_value(expected_value):
    def _check_actual_value(actual_value):
        if expected_value is None:
            return actual_value is None
        else:
            return expected_value == actual_value

    return _check_actual_value


# noinspection PyUnusedLocal
def never(value):
    return False