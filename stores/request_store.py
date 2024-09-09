class RequestStore:
    """
    Interface for a request store to track requests.
    """
    async def get_all_counts(self, key, slot):
        raise NotImplementedError

    async def update_counts(self, key, slot, ttl):
        raise NotImplementedError
