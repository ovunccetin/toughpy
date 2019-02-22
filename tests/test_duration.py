import toughpy as tp


class TestTimeUnits:
    def test_microseconds(self):
        assert tp.microseconds.to_microseconds(1) == 1.0
        assert tp.microseconds.to_milliseconds(1) == 0.001
        assert tp.microseconds.to_seconds(1) == 0.000001
        assert tp.microseconds.to_minutes(1) == 0.000001 / 60
        assert tp.microseconds.to_hours(1) == 0.000001 / 3600
        assert tp.microseconds.to_days(1) == 0.000001 / 86400

    def test_milliseconds(self):
        assert tp.milliseconds.to_microseconds(1) == 1000.0
        assert tp.milliseconds.to_milliseconds(1) == 1
        assert tp.milliseconds.to_seconds(1) == 0.001
        assert tp.milliseconds.to_minutes(1) == 0.001 / 60
        assert tp.milliseconds.to_hours(1) == 0.001 / 3600
        assert tp.milliseconds.to_days(1) == 0.001 / 86400

    def test_seconds(self):
        assert tp.seconds.to_microseconds(1) == 1000000.0
        assert tp.seconds.to_milliseconds(1) == 1000.0
        assert tp.seconds.to_seconds(1) == 1
        assert tp.seconds.to_minutes(1) == 1 / 60
        assert tp.seconds.to_hours(1) == 1 / 3600
        assert tp.seconds.to_days(1) == 1 / 86400

    def test_minutes(self):
        assert tp.minutes.to_microseconds(1) == 60000000.0
        assert tp.minutes.to_milliseconds(1) == 60000.0
        assert tp.minutes.to_seconds(1) == 60
        assert tp.minutes.to_minutes(1) == 1
        assert tp.minutes.to_hours(1) == 1 / 60
        assert tp.minutes.to_days(1) == 1 / 1440

    def test_hours(self):
        assert tp.hours.to_microseconds(1) == 3600000000.0
        assert tp.hours.to_milliseconds(1) == 3600000.0
        assert tp.hours.to_seconds(1) == 3600
        assert tp.hours.to_minutes(1) == 60
        assert tp.hours.to_hours(1) == 1
        assert tp.hours.to_days(1) == 1 / 24

    def test_days(self):
        assert tp.days.to_microseconds(1) == 86400000000.0
        assert tp.days.to_milliseconds(1) == 86400000.0
        assert tp.days.to_seconds(1) == 86400
        assert tp.days.to_minutes(1) == 1440
        assert tp.days.to_hours(1) == 24
        assert tp.days.to_days(1) == 1