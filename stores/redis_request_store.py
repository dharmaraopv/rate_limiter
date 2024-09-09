from redis import Redis
import settings
from stores.request_store import RequestStore


class RedisRequestStore(RequestStore):
    """
    Class to implement request counts storage using Redis. This is responsible for storing
    and managing request counts in Redis for rate limiting purposes.

    Attributes:
        r (Redis): Redis client instance for interacting with Redis.
        num_slots (int): Number of time slots to track requests. Default is 10.
    """

    def __init__(self, redis_url, num_slots=10):
        """
        Initializes the RedisRequestStore object.

        Args:
            redis_url (str): The URL used to connect to the Redis instance.
            num_slots (int): The number of time slots used to track request counts. Default is 10.
        """
        self.r = Redis.from_url(redis_url)
        self.num_slots = num_slots

    def get_all_counts(self, key, slot):
        """
        Retrieves all request counts for a given key (user/token) and time slot from Redis.

        Args:
            key (str): The unique identifier for the user/token.
            slot (int): The current time slot for which counts are being retrieved.

        Returns:
            dict: A dictionary where the keys are the time slots (int) and the values are
            the corresponding request counts (int) for each slot.
        """
        request_counts = self.r.hgetall(key)
        # Convert the request counts from Redis' bytes format to integers
        return {int(k): int(v) for k, v in request_counts.items()}

    def update_counts(self, key, slot, ttl):
        """
        Increments the request count for the given key and time slot in Redis and sets a TTL (time-to-live)
        for the specific slot to expire after the given interval.

        Args:
            key (str): The unique identifier for the user/token.
            slot (int): The time slot for which the request count is being updated.
            ttl (int): Time-to-live for the slot, which defines how long the slot will persist in Redis.
        """
        # Increment the request count for the given key and slot in Redis
        self.r.hincrby(key, slot, 1)
        # Set the expiration for the slot using a custom Redis command to clear the count after TTL
        # This command is supported from Redis 7.4.0 onwards
        self.r.execute_command(f"HEXPIREAT {key} {slot + ttl} FIELDS 1 {slot}")


# Initialize RedisRequestStore with the Redis URL and number of slots from the settings configuration
redis_request_store = RedisRequestStore(redis_url=settings.REDIS_URL, num_slots=settings.NUM_SLOTS)
