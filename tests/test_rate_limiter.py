from rate_limiter import RateLimiter, get_cache_key
from stores.in_mem_request_store import InMemRequestStore
from stores.config_store import config_store, Config
import unittest
from unittest.mock import MagicMock, AsyncMock
import pytest

start_time = 1000000.0


class RateLimiterFunctionalTest(unittest.IsolatedAsyncioTestCase):
    """Functional tests for the RateLimiter class."""

    @pytest.mark.anyio
    async def test_rate_limiter_allow_when_limit_is_not_hit(self):
        """
        This test ensures that two consecutive requests within the allowed limit
        time frame are not rate-limited.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 2 requests per second.
        config_store.set_config(Config(interval=1, limit=2))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 1.0))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 1.0))

    @pytest.mark.anyio
    async def test_rate_limiter_disallow_when_limit_is_hit(self):
        """
        This test ensures that after the allowed limit is reached within the time frame,
        subsequent requests are rate-limited.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 1 request per second.
        config_store.set_config(Config(interval=1, limit=1))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 1.0))
        self.assertTrue(await rate_limiter.is_rate_limited("123", start_time + 1.0))

    @pytest.mark.anyio
    async def test_rate_limiter_allow_requests_in_new_window(self):
        """
        This test ensures that once the time window resets, requests are not rate-limited.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 1 request per second.
        config_store.set_config(Config(interval=1, limit=1))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 1.0))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 2.0))

    @pytest.mark.anyio
    async def test_rate_limiter_disallow_requests_based_on_partial_count_in_previous_window(self):
        """
        Test that the rate limiter disallows requests based on partial counts from the previous window.

        This test checks if the limiter respects the limit when requests fall into an overlapping
        window with partial carry-over counts.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 2 requests over 10 seconds.
        config_store.set_config(Config(interval=10, limit=2))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 1.0))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 1.0))
        self.assertTrue(await rate_limiter.is_rate_limited("123", start_time + 10.1))

    @pytest.mark.anyio
    async def test_rate_limiter_allow_requests_based_on_partial_count_in_previous_window(self):
        """
        Test that the rate limiter allows requests when the partial count from the previous window is within the limit.

        This test ensures that the carry-over from the last slot of the previous window does not result in rate-limiting
        if within the limit.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 2 requests over 10 seconds.
        config_store.set_config(Config(interval=10, limit=2))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 1.0))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 1.0))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 10.6))

    @pytest.mark.anyio
    async def test_rate_limiter_disallow_requests_in_new_window_based_intermediate_slots(self):
        """
        Test that the rate limiter disallows requests in intermediate slots of the current window when the limit is hit.

        This test ensures the limiter respects intermediate slots and rate-limits appropriately.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 2 requests over 10 seconds.
        config_store.set_config(Config(interval=10, limit=2))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 1.0))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 3.0))
        self.assertTrue(await rate_limiter.is_rate_limited("123", start_time + 10))

    @pytest.mark.anyio
    async def test_rate_limiter_allow_requests_in_new_window_based_intermediate_slots(self):
        """
        Test that the rate limiter allows requests in intermediate slots of the current window when the limit is not hit.

        This test ensures that intermediate slots within a new window allow requests if the limit is not exceeded.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 3 requests over 10 seconds.
        config_store.set_config(Config(interval=10, limit=3))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 1.0))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 3.0))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 10))

    @pytest.mark.anyio
    async def test_rate_limiter_keys_should_be_independent(self):
        """
        Test that keys are independent when rate limiting.

        This test ensures that different keys (e.g., different users or tokens) have independent rate limits.
        """
        rate_limiter = RateLimiter(InMemRequestStore(), 10)

        # Set the rate limit to 1 request per second for different keys.
        config_store.set_config(Config(interval=1, limit=1))
        self.assertFalse(await rate_limiter.is_rate_limited("123", start_time + 1.0))
        self.assertFalse(await rate_limiter.is_rate_limited("1234", start_time + 3.0))


class RateLimiterUnitTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Mock the configuration
        self.mock_config = MagicMock()
        self.mock_config.interval = 60  # Assume a 60-second interval
        self.mock_config.limit = 100  # Assume a 100 requests limit

        # Mock the config_store to return the mock_config
        self.mock_config_store = MagicMock()
        self.mock_config_store.get_config.return_value = self.mock_config

        # Mock the RequestStore
        self.mock_request_store = AsyncMock()

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

    @pytest.mark.anyio
    async def test_get_requests_available_no_requests(self):
        # No requests are made yet
        self.mock_request_store.get_all_counts.return_value = {}

        unique_token = 'user123'
        now = 123
        requests_available = await self.rate_limiter.get_requests_available(unique_token, now)

        # Expect full limit to be available
        self.assertEqual(requests_available, self.mock_config.limit)

    @pytest.mark.anyio
    async def test_get_requests_available_with_requests(self):
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

        requests_available = await self.rate_limiter.get_requests_available(unique_token, now)

        # Expect limit minus the total count of requests
        total_requests = 15 + 30
        self.assertEqual(requests_available, self.mock_config.limit - total_requests)

    @pytest.mark.anyio
    async def test_is_rate_limited_not_limited(self):
        unique_token = 'user123'
        now = 123

        # Mock to return that requests are still available
        self.rate_limiter.get_requests_available = AsyncMock(return_value=50)

        is_limited = await self.rate_limiter.is_rate_limited(unique_token, now)

        self.assertFalse(is_limited)
        self.rate_limiter.get_requests_available.assert_called_once_with(unique_token, now)
        # Ensure that update_counts is called when not rate-limited
        self.mock_request_store.update_counts.assert_called_once_with(unique_token, self.rate_limiter.get_slot(now),
                                                                      self.mock_config.interval)

    @pytest.mark.anyio
    async def test_is_rate_limited_false_when_no_available_requests(self):
        """
        In this scenario, since the check happens after updating the counts,
        rate limiting is not hit on 0 requests available.
        """
        unique_token = 'user123'
        now = 123

        # Mock to return that no requests are available (rate limited)
        self.rate_limiter.get_requests_available = AsyncMock(return_value=0)

        is_limited = await self.rate_limiter.is_rate_limited(unique_token, now)

        self.assertFalse(is_limited)
        self.rate_limiter.get_requests_available.assert_called_once_with(unique_token, now)
        # Ensure that update_counts is called when not rate-limited
        self.mock_request_store.update_counts.assert_called()

    @pytest.mark.anyio
    async def test_is_rate_limited_true_negative_available_requests(self):
        unique_token = 'user123'
        now = 123

        # Mock to return that no requests are available (rate limited)
        self.rate_limiter.get_requests_available = AsyncMock(return_value=-5)

        is_limited = await self.rate_limiter.is_rate_limited(unique_token, now)

        self.assertTrue(is_limited)
        self.rate_limiter.get_requests_available.assert_called_once_with(unique_token, now)
        # Ensure that update_counts is not called if rate-limited
        self.mock_request_store.update_counts.assert_called()

    @pytest.mark.anyio
    async def test_is_rate_limited_cached(self):
        unique_token = 'user123'
        now = 123
        slot = self.rate_limiter.get_slot(now)

        # Mock that the token is cached as blocked
        self.rate_limiter.is_blocked_cached = MagicMock(return_value=True)
        self.rate_limiter.get_requests_available = MagicMock()

        # Check if the token is rate-limited based on the cache
        is_limited = await self.rate_limiter.is_rate_limited(unique_token, now)

        self.assertTrue(is_limited)
        self.rate_limiter.is_blocked_cached.assert_called_once_with(unique_token, slot)
        self.rate_limiter.get_requests_available.assert_not_called()

    @pytest.mark.anyio
    async def test_update_counts(self):
        unique_token = 'user123'
        slot = 5


        # Call update_counts
        await self.rate_limiter.update_counts(unique_token, slot)

        # Ensure update_counts on the request store was called with the correct slot
        self.mock_request_store.update_counts.assert_called_once_with(unique_token, slot, self.mock_config.interval)

    def test_is_blocked_cached_true(self):
        unique_token = 'user123'
        slot = 5
        cache_key = f'{unique_token}-{slot}'

        # Mock the cache to return True for a blocked token
        self.rate_limiter.blocked_tokens_cache.get = MagicMock(return_value=True)

        result = self.rate_limiter.is_blocked_cached(unique_token, slot)

        self.rate_limiter.blocked_tokens_cache.get.assert_called_once_with(cache_key)
        self.assertTrue(result)

    def test_is_blocked_cached_false(self):
        unique_token = 'user123'
        slot = 5
        cache_key = f'{unique_token}-{slot}'

        # Mock the cache to return False for a non-blocked token
        self.rate_limiter.blocked_tokens_cache.get = MagicMock(return_value=None)

        result = self.rate_limiter.is_blocked_cached(unique_token, slot)

        self.rate_limiter.blocked_tokens_cache.get.assert_called_once_with(cache_key)
        self.assertFalse(result)

    def test_set_blocked_cache(self):
        unique_token = 'user123'
        slot = 5
        cache_key = f'{unique_token}-{slot}'

        self.rate_limiter.blocked_tokens_cache.set = MagicMock()

        # Call set_blocked_cache
        self.rate_limiter.set_blocked_cache(unique_token, slot)

        # Ensure the blocked token is set in the cache with True value
        self.rate_limiter.blocked_tokens_cache.set.assert_called_once_with(cache_key, True)

    def test_get_cache_key(self):
        unique_token = 'user123'
        slot = 5
        expected_cache_key = f'{unique_token}-{slot}'

        # Test if the cache key is generated correctly
        cache_key = get_cache_key(slot, unique_token)

        self.assertEqual(cache_key, expected_cache_key)

if __name__ == '__main__':
    unittest.main()
