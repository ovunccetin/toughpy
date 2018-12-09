import inspect


def pytest_itemcollected(item):
    parent = item.parent.obj
    node = item.obj

    parent_label = _get_parent_label(parent)
    test_label = _get_test_label(node)
    if test_label:
        item._nodeid = bold(magenta(' + ')) + bold(parent_label) + ': ' + cyan(test_label)


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


def _get_test_label(node):
    label = node.__doc__ if node.__doc__ else node.__name__

    lines = filter(
        lambda l: len(l) > 0,
        [line.strip() for line in label.splitlines()]
    )

    first = True
    line_list = []
    for line in lines:
        if first:
            line_list.append(line)
            first = False
        else:
            line_list.append('   ' + line)

    return '\n'.join(line_list)


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


def bold(text):
    return colorize(text, BOLD)
