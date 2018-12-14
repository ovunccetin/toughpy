_1K = 1000
_1M = _1K * _1K
_1B = _1M * _1K


class Duration:

    def __init__(self, length, unit):
        self._length = length
        self._unit = unit

    @property
    def length(self):
        return self._length

    @property
    def unit(self):
        return self._unit

    def to_micros(self):
        return self._unit.to_microseconds(self._length)

    def to_millis(self):
        return self._unit.to_milliseconds(self._length)

    def to_seconds(self):
        return self._unit.to_seconds(self._length)

    def to_minutes(self):
        return self._unit.to_minutes(self._length)

    def to_hours(self):
        return self._unit.to_hours(self._length)

    def to_days(self):
        return self._unit.to_days(self._length)

    def __str__(self):
        return '%s %ss' % (self.length, self.unit.__name__)


class TimeUnit:
    @staticmethod
    def to_nanoseconds(value): pass

    @staticmethod
    def to_microseconds(value): pass

    @staticmethod
    def to_milliseconds(value): pass

    @staticmethod
    def to_seconds(value): pass

    @staticmethod
    def to_minutes(value): pass

    @staticmethod
    def to_hours(value): pass

    @staticmethod
    def to_days(value): pass


class microseconds(TimeUnit):
    @staticmethod
    def to_nanoseconds(value):
        return float(value) * _1K

    @staticmethod
    def to_microseconds(value):
        return float(value)

    @staticmethod
    def to_milliseconds(value):
        return float(value) / _1K

    @staticmethod
    def to_seconds(value):
        return float(value) / _1M

    @staticmethod
    def to_minutes(value):
        return float(value) / _1M / 60

    @staticmethod
    def to_hours(value):
        return float(value) / _1M / 3600

    @staticmethod
    def to_days(value):
        return float(value) / _1M / 86400


class milliseconds(TimeUnit):
    @staticmethod
    def to_nanoseconds(value):
        return float(value) * _1M

    @staticmethod
    def to_microseconds(value):
        return float(value) * _1K

    @staticmethod
    def to_milliseconds(value):
        return float(value)

    @staticmethod
    def to_seconds(value):
        return float(value) / _1K

    @staticmethod
    def to_minutes(value):
        return float(value) / _1K / 60

    @staticmethod
    def to_hours(value):
        return float(value) / _1K / 3600

    @staticmethod
    def to_days(value):
        return float(value) / _1K / 86400


class seconds(TimeUnit):
    @staticmethod
    def to_nanoseconds(value):
        return float(value) * _1B

    @staticmethod
    def to_microseconds(value):
        return float(value) * _1M

    @staticmethod
    def to_milliseconds(value):
        return float(value) * _1K

    @staticmethod
    def to_seconds(value):
        return float(value)

    @staticmethod
    def to_minutes(value):
        return float(value) / 60

    @staticmethod
    def to_hours(value):
        return float(value) / 3600

    @staticmethod
    def to_days(value):
        return float(value) / 86400


class minutes(TimeUnit):
    @staticmethod
    def to_nanoseconds(value):
        return float(value) * _1B * 60

    @staticmethod
    def to_microseconds(value):
        return float(value) * _1M * 60

    @staticmethod
    def to_milliseconds(value):
        return float(value) * _1K * 60

    @staticmethod
    def to_seconds(value):
        return float(value) * 60

    @staticmethod
    def to_minutes(value):
        return float(value)

    @staticmethod
    def to_hours(value):
        return float(value) / 60

    @staticmethod
    def to_days(value):
        return float(value) / 1440


class hours(TimeUnit):
    @staticmethod
    def to_nanoseconds(value):
        return float(value) * _1B * 3600

    @staticmethod
    def to_microseconds(value):
        return float(value) * _1M * 3600

    @staticmethod
    def to_milliseconds(value):
        return float(value) * _1K * 3600

    @staticmethod
    def to_seconds(value):
        return float(value) * 3600

    @staticmethod
    def to_minutes(value):
        return float(value) * 60

    @staticmethod
    def to_hours(value):
        return float(value)

    @staticmethod
    def to_days(value):
        return float(value) / 24


class days(TimeUnit):
    @staticmethod
    def to_nanoseconds(value):
        return float(value) * _1B * 86400

    @staticmethod
    def to_microseconds(value):
        return float(value) * _1M * 86400

    @staticmethod
    def to_milliseconds(value):
        return float(value) * _1K * 86400

    @staticmethod
    def to_seconds(value):
        return float(value) * 86400

    @staticmethod
    def to_minutes(value):
        return float(value) * 1440

    @staticmethod
    def to_hours(value):
        return float(value) * 24

    @staticmethod
    def to_days(value):
        return float(value)
