from .retry import Retry, RetryError
from .duration import Duration, TimeUnit
import toughpy.duration as duration
import toughpy.utils as u

retry = retry
random_delay = retry.backoffs.random_delay
linear_delay = retry.backoffs.linear_delay
exponential_delay = retry.backoffs.exponential_delay

microseconds = duration.microseconds
milliseconds = duration.milliseconds
seconds = duration.seconds
minutes = duration.minutes
hours = duration.hours
days = duration.days
