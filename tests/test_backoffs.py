import tough.backoffs as backoffs


def test_fixed_backoff():
    backoff = backoffs.FixedBackoff(3)
    assert backoff.get_delay(attempt_number=1) == 3
    assert backoff.get_delay(attempt_number=10) == 3


def test_fixed_list_backoff():
    backoff = backoffs.FixedListBackoff([2, 5, 8])
    assert backoff.get_delay(attempt_number=1) == 2
    assert backoff.get_delay(attempt_number=2) == 5
    assert backoff.get_delay(attempt_number=3) == 8

    for x in range(4, 100):
        assert backoff.get_delay(attempt_number=x) == 8


def test_random_backoff():
    backoff = backoffs.RandomBackoff(min_seconds=2, max_seconds=5)

    for x in range(1, 100):
        delay = backoff.get_delay(attempt_number=x)
        assert 2.0 <= delay <= 5.0


def test_linear_backoff():
    backoff = backoffs.LinearBackoff(initial_delay=0.1, increase=0.3)

    assert backoff.get_delay(attempt_number=1) == 0.1
    assert backoff.get_delay(attempt_number=2) == 0.1 + 0.3
    assert backoff.get_delay(attempt_number=3) == 0.1 + 0.3 + 0.3

    for x in range(1, 100):
        assert backoff.get_delay(attempt_number=x) == 0.1 + 0.3 * (x - 1)


def test_linear_backoff_with_random():
    backoff = backoffs.LinearBackoff(initial_delay=1, increase=3, randomizer=(0.3, 1.2))

    for x in range(1, 10):
        base_delay = 1.0 + 3 * (x - 1)
        for _ in range(10):
            delay = backoff.get_delay(attempt_number=x)
            assert base_delay + 0.3 <= delay <= base_delay + 1.2


def test_exponential_backoff():
    backoff = backoffs.ExponentialBackoff(initial_delay=0.3, base=2)

    assert backoff.get_delay(attempt_number=1) == 0.3
    assert backoff.get_delay(attempt_number=2) == 0.3 * 2 ** 1
    assert backoff.get_delay(attempt_number=3) == 0.3 * 2 ** 2

    for x in range(1, 10):
        assert backoff.get_delay(attempt_number=x) == 0.3 * 2 ** (x - 1)


def test_exponential_backoff_with_random():
    backoff = backoffs.ExponentialBackoff(initial_delay=0.7, base=2, randomizer=(0.3, 1.2))

    for x in range(1, 10):
        base_delay = 0.7 * 2 ** (x - 1)
        for _ in range(10):
            delay = backoff.get_delay(attempt_number=x)
            assert base_delay + 0.3 <= delay <= base_delay + 1.2


def test_fibonacci_backoff():
    backoff = backoffs.FibonacciBackoff(1, 2)

    assert backoff.get_delay(attempt_number=1) == 1
    assert backoff.get_delay(attempt_number=2) == 2
    assert backoff.get_delay(attempt_number=3) == 3
    assert backoff.get_delay(attempt_number=4) == 5
    assert backoff.get_delay(attempt_number=5) == 8
    assert backoff.get_delay(attempt_number=6) == 13


def test_create_backoff():
    fn = backoffs.create_backoff(given=None)
    assert fn.__name__ == 'fixed'
    assert fn(attempt_no=10) == backoffs.DEFAULT_FIXED_DELAY

    fn = backoffs.create_backoff(given=None, default=0.3)
    assert fn.__name__ == 'fixed'
    assert fn(attempt_no=10) == 0.3

    fn = backoffs.create_backoff(given=None, default=backoffs.exponential(0.1))
    assert fn.__name__ == 'exponential'

    fn = backoffs.create_backoff(given=0.7)
    assert fn.__name__ == 'fixed'
    assert fn(attempt_no=10) == 0.7

    fn = backoffs.create_backoff(given=[1, 2, 5])
    assert fn.__name__ == 'fixed_list'
    assert fn(attempt_no=10) == 5

    def custom_delay(attempt_no): return attempt_no

    fn = backoffs.create_backoff(given=custom_delay)
    assert fn.__name__ == 'custom_delay'
    assert fn(attempt_no=10) == 10
