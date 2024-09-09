class RequestStore:
    """
    Interface for a request store to track requests.
    """
    def get_all_counts(self, key, slot):
        raise NotImplementedError

    def update_counts(self, key, slot, ttl):
        raise NotImplementedError
