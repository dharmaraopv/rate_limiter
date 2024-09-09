from stores.config_store import config_store
from stores.request_store import RequestStore
import settings
import math


class RateLimiter:
    """
    Class to implement rate limiting functionality. It limits the number of requests
    that can be made with a unique token within a given time interval, based on the configuration settings.

    Attributes:
        request_store (RequestStore): Object to manage and store request counts.
        num_slots (int): Number of time slots to track requests. Default is 10.
        config_store: Configuration store to access rate limiter settings.
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

    @property
    def config(self):
        """
        Fetches the configuration for the rate limiter from the config store.

        Returns:
            Config object containing interval and limit settings.
        """
        return self.config_store.get_config()

    def partial_count_oldest_slot(self, now, oldest_count):
        """
        Calculates a partial count for requests in the oldest time slot,
        adjusting based on how far into the interval the current time is.

        Args:
            now (int): Current time (in seconds or appropriate time unit).
            oldest_count (int): Count of requests in the oldest time slot.

        Returns:
            int: Adjusted count of requests for the oldest slot.
        """
        return math.ceil(oldest_count * (1 - (now * 10 % self.config.interval) / self.config.interval))

    def get_slot(self, now):
        """
        Calculates which time slot the current time falls into.

        Args:
            now (int): Current time.

        Returns:
            int: The current time slot index.
        """
        return int(now * 10) // self.config.interval

    def get_requests_available(self, unique_token: str, now: int):
        """
        Determines the number of requests available to a token for the current time slot.

        Args:
            unique_token (str): Unique identifier for the user/token.
            now (int): Current time.

        Returns:
            int: The number of requests remaining for the user/token based on rate limits.
        """
        slot = self.get_slot(now)
        request_counts = self.request_store.get_all_counts(unique_token, slot)
        if not request_counts:
            # If no requests are found, return the limit
            return self.config.limit

        count = 0
        # Check if there are requests in the oldest slot and adjust them accordingly
        if slot - self.num_slots + 1 in request_counts:
            count = self.partial_count_oldest_slot(now, request_counts.pop(slot - self.num_slots + 1))

        # Sum up the remaining requests from other slots
        count += sum(request_counts.values())

        return self.config.limit - count

    def is_rate_limited(self, unique_token, now, background_tasks):
        """
        Checks if the user/token is rate limited at the current time.

        Args:
            unique_token (str): Unique identifier for the user/token.
            now (int): Current time.
            background_tasks: Task scheduler to handle updating counts in the background.

        Returns:
            bool: True if the user/token is rate-limited, False otherwise.
        """
        status = self.get_requests_available(unique_token, now) <= 0

        if not status:
            # Update the request counts only if not rate-limited
            if settings.DO_UPDATES_IN_BACKGROUND and False:
                background_tasks.add_task(self.update_counts, unique_token, now)
            else:
                self.update_counts(unique_token, now)
        return status

    def update_counts(self, key, now):
        """
        Updates the request count for a specific user/token and time slot.

        Args:
            key (str): Unique identifier for the user/token.
            now (int): Current time.

        Returns:
            Updated count in the request store.
        """
        slot = self.get_slot(now)
        return self.request_store.update_counts(key, slot, self.config.interval)


# Instantiate RateLimiter with appropriate storage based on settings
if settings.STORAGE_TYPE == "redis":
    from stores.redis_request_store import redis_request_store

    rate_limiter = RateLimiter(redis_request_store)
else:
    from stores.in_mem_request_store import InMemRequestStore

    rate_limiter = RateLimiter(InMemRequestStore())
