import settings
from stores.lru_store import LRUStore
from stores.request_store import RequestStore


class RequestCounter:
    """
    Class to keep track of request counts within specific time slots.
    The counter is a LRUStore with a capacity of num_slots.
    """

    def __init__(self, num_slots=10):
        self.counter = LRUStore(capacity=num_slots)
        self.current_slot = -1
        self.num_slots = num_slots

    def __repr__(self):
        return f"RequestCounter({self.counter})"

    def increment(self, slot, ttl):
        previous_count = 0
        if slot == self.current_slot:
            latest_entry = self.counter.get(slot)
            if latest_entry is not None:
                previous_count = latest_entry
        else:
            self.current_slot = slot

        self.counter.set(slot, (previous_count + 1))

    def get_all_counts(self, slot):
        all_counts = self.counter.get_all()
        return {i: all_counts[i] for i in range(slot - self.num_slots + 1, slot + 1) if i in all_counts}


class InMemRequestStore(RequestStore):
    """
    Class to implement request counts storage in memory. This is responsible for storing
    and managing request counts in memory for rate limiting purposes.

    To be used for testing and development purposes.
    """
    def __init__(self, num_slots=10, capacity=1000):
        self.num_slots = num_slots
        self.store = LRUStore(capacity=capacity)

    async def get_all_counts(self, key, slot):
        request_counter = self.store.get(key)
        if request_counter is None:
            return {}
        return request_counter.get_all_counts(slot)

    async def update_counts(self, key, slot, ttl):
        request_counter = self.store.get(key)
        if request_counter is None:
            request_counter = RequestCounter(num_slots=self.num_slots)
            self.store.set(key, request_counter)
        request_counter.increment(slot, ttl)


in_mem_request_store = InMemRequestStore(num_slots=settings.NUM_SLOTS, capacity=settings.IN_MEM_CAPACITY)
