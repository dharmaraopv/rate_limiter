from stores.config_store import config_store
from stores.lru_store import LRUStore
from stores.request_store import RequestStore
import settings


def get_cache_key(slot, unique_token):
    cache_key = f"{unique_token}-{slot}"
    return cache_key


class RateLimiter:
    """
    Class to implement rate limiting functionality. It limits the number of requests
    that can be made with a unique token within a given time interval, based on the configuration settings.

    Attributes:
        request_store (RequestStore): Object to manage and store request counts.
        num_slots (int): Number of time slots to track requests. Default is 10.
        config_store: Configuration store to access rate limiter settings.
        blocked_tokens_cache: Cache to store blocked tokens in a given time slot.
    """

    def __init__(self, request_store: RequestStore, num_slots=10, config=config_store):
        """
        Initializes a RateLimiter instance.

        Args:
            request_store (RequestStore): An instance of RequestStore to track requests.
            num_slots (int): Number of time slots to track. Default is 10.
            config: Configuration for rate limiting, which includes the interval and request limits.
        """
        self.request_store = request_store
        self.num_slots = num_slots
        self.config_store = config
        self.blocked_tokens_cache = LRUStore(capacity=10000)

    @property
    def config(self):
        """
        Fetches the configuration for the rate limiter from the config store.

        Returns:
            Config object containing interval and limit settings.
        """
        return self.config_store.get_config()

    def get_slot(self, now):
        """
        Calculates which time slot the current time falls into.

        Args:
            now (int): Current time.

        Returns:
            int: The current time slot index.
        """
        return int(now * 10) // self.config.interval

    async def get_requests_available(self, unique_token: str, now: int):
        """
        Determines the number of requests available to a token for the current time slot.

        Args:
            unique_token (str): Unique identifier for the user/token.
            now (int): Current time.

        Returns:
            int: The number of requests remaining for the user/token based on rate limits.
        """
        slot = self.get_slot(now)
        request_counts = await self.request_store.get_all_counts(unique_token, slot)
        if not request_counts:
            # If no requests are found, return the limit
            return self.config.limit

        # Sum up the remaining requests from other slots
        count = sum(request_counts.values())

        return self.config.limit - count

    async def is_rate_limited(self, unique_token, now):
        """
        Checks if the user/token is rate limited at the current time.

        Args:
            unique_token (str): Unique identifier for the user/token.
            now (float): Current time.

        Returns:
            bool: True if the user/token is rate-limited, False otherwise.
        """
        slot = self.get_slot(now)
        # Get the blocked status from the cache
        if self.is_blocked_cached(unique_token, slot):
            return True

        # Ideally update the request counts only if not rate-limited
        # But there is an edge case, where we might update the counts if even after hitting the limit
        await self.update_counts(unique_token, slot)

        available_requests = await self.get_requests_available(unique_token, now)

        if available_requests <= 0:
            self.set_blocked_cache(unique_token, slot)
        return available_requests < 0

    async def update_counts(self, key, slot):
        """
        Updates the request count for a specific user/token and time slot.

        Args:
            key (str): Unique identifier for the user/token.
            slot (int): Current timeslot.

        Returns:
            Updated count in the request store.
        """
        return await self.request_store.update_counts(key, slot, self.config.interval)

    def is_blocked_cached(self, unique_token, slot):
        cache_key = get_cache_key(slot, unique_token)
        if self.blocked_tokens_cache.get(cache_key):
            return True
        return False

    def set_blocked_cache(self, unique_token, slot):
        cache_key = get_cache_key(slot, unique_token)
        self.blocked_tokens_cache.set(cache_key, True)


# Instantiate RateLimiter with appropriate storage based on settings
if settings.STORAGE_TYPE == "redis":
    from stores.redis_request_store import redis_request_store

    rate_limiter = RateLimiter(redis_request_store)
else:
    from stores.in_mem_request_store import InMemRequestStore

    rate_limiter = RateLimiter(InMemRequestStore())
