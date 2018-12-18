import inspect


def pytest_itemcollected(item):
    parent = item.parent.obj
    node = item.obj

    test_name = node.__name__
    test_desc = node.__doc__
    parent_label = _get_parent_label(parent)

    txt = bold(magenta(' + ')) + bold(parent_label) + ': ' + cyan(test_name)

    if not test_desc:
        item._nodeid = txt
    else:
        item._nodeid = txt + ': ' + gray(test_desc)


def _get_parent_label(parent):
    if parent.__doc__:
        label = parent.__doc__
    elif inspect.ismodule(parent):
        label = parent.__name__.split('.')[-1]
    elif isinstance(parent, object):
        cls = parent.__class__
        mdl = cls.__module__.split('.')[-1]
        label = mdl + '.' + cls.__name__
    else:
        label = "<unknown>"

    label = label.replace('test_', '')

    return label


def _calc_number_of_extra_spaces(lines):
    min_spaces = 1000
    for line in lines:
        if line:
            lspaces = len(line) - len(line.lstrip())
            if lspaces < min_spaces:
                min_spaces = lspaces

    return min_spaces if min_spaces < 1000 else 0


BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'
GRAY = '\033[90m'

BOLD = '\033[1m'
RESET = '\033[0m'


def colorize(text, color):
    return color + text + RESET


def magenta(text):
    return colorize(text, MAGENTA)


def cyan(text):
    return colorize(text, CYAN)


def gray(text):
    return colorize(text, GRAY)


def bold(text):
    return colorize(text, BOLD)
