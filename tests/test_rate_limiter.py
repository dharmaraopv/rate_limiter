from .utils import test_bg_tasks
from rate_limiter import RateLimiter
from stores.in_mem_request_store import InMemRequestStore
from stores.config_store import config_store, Config
import unittest
from unittest.mock import MagicMock

start_time = 1000000.0


class RateLimiterFunctionalTest(unittest.TestCase):
    """Functional tests for the RateLimiter class."""

    def test_rate_limiter_allow_when_limit_is_not_hit(self):
        """
        This test ensures that two consecutive requests within the allowed limit
        time frame are not rate-limited.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 2 requests per second.
        config_store.set_config(Config(interval=1, limit=2))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 1.0, test_bg_tasks))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 1.0, test_bg_tasks))

    def test_rate_limiter_disallow_when_limit_is_hit(self):
        """
        This test ensures that after the allowed limit is reached within the time frame,
        subsequent requests are rate-limited.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 1 request per second.
        config_store.set_config(Config(interval=1, limit=1))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 1.0, test_bg_tasks))
        self.assertTrue(rate_limiter.is_rate_limited("123", start_time + 1.0, test_bg_tasks))

    def test_rate_limiter_allow_requests_in_new_window(self):
        """
        This test ensures that once the time window resets, requests are not rate-limited.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 1 request per second.
        config_store.set_config(Config(interval=1, limit=1))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 1.0, test_bg_tasks))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 2.0, test_bg_tasks))

    def test_rate_limiter_disallow_requests_based_on_partial_count_in_previous_window(self):
        """
        Test that the rate limiter disallows requests based on partial counts from the previous window.

        This test checks if the limiter respects the limit when requests fall into an overlapping
        window with partial carry-over counts.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 2 requests over 10 seconds.
        config_store.set_config(Config(interval=10, limit=2))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 1.0, test_bg_tasks))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 1.0, test_bg_tasks))
        self.assertTrue(rate_limiter.is_rate_limited("123", start_time + 10.1, test_bg_tasks))

    def test_rate_limiter_allow_requests_based_on_partial_count_in_previous_window(self):
        """
        Test that the rate limiter allows requests when the partial count from the previous window is within the limit.

        This test ensures that the carry-over from the last slot of the previous window does not result in rate-limiting
        if within the limit.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 2 requests over 10 seconds.
        config_store.set_config(Config(interval=10, limit=2))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 1.0, test_bg_tasks))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 1.0, test_bg_tasks))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 10.6, test_bg_tasks))

    def test_rate_limiter_disallow_requests_in_new_window_based_intermediate_slots(self):
        """
        Test that the rate limiter disallows requests in intermediate slots of the current window when the limit is hit.

        This test ensures the limiter respects intermediate slots and rate-limits appropriately.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 2 requests over 10 seconds.
        config_store.set_config(Config(interval=10, limit=2))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 1.0, test_bg_tasks))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 3.0, test_bg_tasks))
        self.assertTrue(rate_limiter.is_rate_limited("123", start_time + 10, test_bg_tasks))

    def test_rate_limiter_allow_requests_in_new_window_based_intermediate_slots(self):
        """
        Test that the rate limiter allows requests in intermediate slots of the current window when the limit is not hit.

        This test ensures that intermediate slots within a new window allow requests if the limit is not exceeded.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 3 requests over 10 seconds.
        config_store.set_config(Config(interval=10, limit=3))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 1.0, test_bg_tasks))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 3.0, test_bg_tasks))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 10, test_bg_tasks))

    def test_rate_limiter_keys_should_be_independent(self):
        """
        Test that keys are independent when rate limiting.

        This test ensures that different keys (e.g., different users or tokens) have independent rate limits.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 1 request per second for different keys.
        config_store.set_config(Config(interval=1, limit=1))
        self.assertFalse(rate_limiter.is_rate_limited("123", start_time + 1.0, test_bg_tasks))
        self.assertFalse(rate_limiter.is_rate_limited("1234", start_time + 3.0, test_bg_tasks))


class RateLimiterUnitTest(unittest.TestCase):

    def setUp(self):
        # Mock the configuration
        self.mock_config = MagicMock()
        self.mock_config.interval = 60  # Assume a 60-second interval
        self.mock_config.limit = 100  # Assume a 100 requests limit

        # Mock the config_store to return the mock_config
        self.mock_config_store = MagicMock()
        self.mock_config_store.get_config.return_value = self.mock_config

        # Mock the RequestStore
        self.mock_request_store = MagicMock()

        # Instantiate RateLimiter with mock objects
        self.rate_limiter = RateLimiter(self.mock_request_store, config=self.mock_config_store)

    def test_config_property(self):
        # Ensure the config is fetched from the config store
        config = self.rate_limiter.config
        self.mock_config_store.get_config.assert_called_once()
        self.assertEqual(config.interval, 60)
        self.assertEqual(config.limit, 100)

    def test_partial_count_oldest_slot(self):
        # Testing partial count calculation with known values
        now = 123
        oldest_count = 50
        partial_count = self.rate_limiter.partial_count_oldest_slot(now, oldest_count)
        self.assertEqual(partial_count, 25)

    def test_get_slot(self):
        # Testing slot calculation
        now = 123
        slot = self.rate_limiter.get_slot(now)
        self.assertEqual(slot, 20)

    def test_get_requests_available_no_requests(self):
        # No requests are made yet
        self.mock_request_store.get_all_counts.return_value = {}

        unique_token = 'user123'
        now = 123
        requests_available = self.rate_limiter.get_requests_available(unique_token, now)

        # Expect full limit to be available
        self.assertEqual(requests_available, self.mock_config.limit)

    def test_get_requests_available_with_requests(self):
        # Mock some request counts for the current slot and oldest slot
        self.mock_request_store.get_all_counts.return_value = {
            11: 20,  # Oldest slot
            12: 30  # Another slot
        }
        unique_token = 'user123'
        now = 123
        self.mock_config.interval = 60

        # Partial count for the oldest slot
        self.rate_limiter.partial_count_oldest_slot = MagicMock(return_value=15)

        requests_available = self.rate_limiter.get_requests_available(unique_token, now)

        # Expect limit minus the total count of requests
        total_requests = 15 + 30
        self.assertEqual(requests_available, self.mock_config.limit - total_requests)

    def test_is_rate_limited_not_limited(self):
        unique_token = 'user123'
        now = 123
        background_tasks = MagicMock()

        # Mock to return that requests are still available
        self.rate_limiter.get_requests_available = MagicMock(return_value=50)

        is_limited = self.rate_limiter.is_rate_limited(unique_token, now, background_tasks)

        self.assertFalse(is_limited)
        self.rate_limiter.get_requests_available.assert_called_once_with(unique_token, now)
        # Ensure that update_counts is called when not rate-limited
        self.mock_request_store.update_counts.assert_called_once_with(unique_token, self.rate_limiter.get_slot(now),
                                                                      self.mock_config.interval)

    def test_is_rate_limited_true(self):
        unique_token = 'user123'
        now = 123
        background_tasks = MagicMock()

        # Mock to return that no requests are available (rate limited)
        self.rate_limiter.get_requests_available = MagicMock(return_value=0)

        is_limited = self.rate_limiter.is_rate_limited(unique_token, now, background_tasks)

        self.assertTrue(is_limited)
        self.rate_limiter.get_requests_available.assert_called_once_with(unique_token, now)
        # Ensure that update_counts is not called if rate-limited
        self.mock_request_store.update_counts.assert_not_called()

    def test_update_counts(self):
        unique_token = 'user123'
        now = 123

        # Mock slot calculation
        self.rate_limiter.get_slot = MagicMock(return_value=5)

        # Call update_counts
        self.rate_limiter.update_counts(unique_token, now)

        # Ensure update_counts on the request store was called with the correct slot
        self.mock_request_store.update_counts.assert_called_once_with(unique_token, 5, self.mock_config.interval)


if __name__ == '__main__':
    unittest.main()
