import unittest
from unittest.mock import patch, MagicMock
from stores.redis_request_store import RedisRequestStore  # Adjust import based on your project structure


class TestRedisRequestStore(unittest.TestCase):
    @patch('redis.Redis.from_url')
    def setUp(self, mock_redis_from_url):
        """
        Set up a mock Redis instance and initialize RedisRequestStore.
        """
        self.mock_redis = MagicMock()
        mock_redis_from_url.return_value = self.mock_redis
        self.redis_store = RedisRequestStore(redis_url="mock_redis_url", num_slots=10)

    def test_get_all_counts(self):
        """
        Test the get_all_counts method to ensure correct retrieval of request counts.
        """
        # Mock Redis hgetall return value
        self.mock_redis.hgetall.return_value = {b'1': b'5', b'2': b'10'}

        key = "test_key"
        slot = 2

        # Expected return is a dictionary with integer keys and values
        expected_result = {1: 5, 2: 10}

        result = self.redis_store.get_all_counts(key, slot)

        # Assert that the result matches the expected dictionary
        self.assertEqual(result, expected_result)

        # Ensure hgetall was called with the correct key
        self.mock_redis.hgetall.assert_called_with(key)

    def test_update_counts(self):
        """
        Test the update_counts method to ensure it increments the count and sets the expiration.
        """
        key = "test_key"
        slot = 3
        ttl = 100

        # Call the update_counts method
        self.redis_store.update_counts(key, slot, ttl)

        # Assert hincrby was called with the correct parameters
        self.mock_redis.hincrby.assert_called_with(key, slot, 1)

        # Assert execute_command was called to set expiration
        expected_command = f"HEXPIREAT test_key 103 FIELDS 1 3"
        self.mock_redis.execute_command.assert_called_with(expected_command)

    def test_get_all_counts_empty(self):
        """
        Test get_all_counts method when no data is returned from Redis.
        """
        # Mock Redis hgetall return value
        self.mock_redis.hgetall.return_value = {}

        key = "test_key"
        slot = 5

        # Should return an empty dictionary when no data is available
        result = self.redis_store.get_all_counts(key, slot)
        self.assertEqual(result, {})

        # Ensure hgetall was called with the correct key
        self.mock_redis.hgetall.assert_called_with(key)


if __name__ == '__main__':
    unittest.main()
