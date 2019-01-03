import tough.common.backoffs as backoffs


def test_fixed():
    fixed_backoff = backoffs.fixed(3)
    assert fixed_backoff(attempt_no=1) == 3
    assert fixed_backoff(attempt_no=10) == 3


def test_fixed_list():
    fixed_list_backoff = backoffs.fixed_list([2, 5, 8])
    assert fixed_list_backoff(attempt_no=1) == 2
    assert fixed_list_backoff(attempt_no=2) == 5
    assert fixed_list_backoff(attempt_no=3) == 8

    for x in range(4, 100):
        assert fixed_list_backoff(attempt_no=x) == 8


def test_random():
    random_backoff = backoffs.random(2, 5)

    for x in range(1, 100):
        delay = random_backoff(attempt_no=x)
        assert 2.0 <= delay <= 5.0


def test_linear():
    linear_backoff = backoffs.linear(initial=0.1, accrual=0.3)

    assert linear_backoff(attempt_no=1) == 0.1
    assert linear_backoff(attempt_no=2) == 0.1 + 0.3
    assert linear_backoff(attempt_no=3) == 0.1 + 0.3 + 0.3

    for x in range(1, 100):
        assert linear_backoff(attempt_no=x) == 0.1 + 0.3 * (x - 1)


def test_linear_with_random():
    linear_backoff = backoffs.linear(initial=1, accrual=3, randomizer=(0.3, 1.2))

    for x in range(1, 10):
        base_delay = 1.0 + 3 * (x - 1)
        for _ in range(10):
            delay = linear_backoff(attempt_no=x)
            assert base_delay + 0.3 <= delay <= base_delay + 1.2


def test_exponential():
    exp_backoff = backoffs.exponential(initial=0.3, base=2)

    assert exp_backoff(attempt_no=1) == 0.3
    assert exp_backoff(attempt_no=2) == 0.3 * 2 ** 1
    assert exp_backoff(attempt_no=3) == 0.3 * 2 ** 2

    for x in range(1, 10):
        assert exp_backoff(attempt_no=x) == 0.3 * 2 ** (x - 1)


def test_exponential_with_random():
    exp_backoff = backoffs.exponential(initial=0.7, base=2, randomizer=(0.3, 1.2))

    for x in range(1, 10):
        base_delay = 0.7 * 2 ** (x - 1)
        for _ in range(10):
            delay = exp_backoff(attempt_no=x)
            assert base_delay + 0.3 <= delay <= base_delay + 1.2


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
