from collections import OrderedDict


class LRUStore:
    def __init__(self, capacity=1000):
        self.capacity = capacity
        self.store = OrderedDict()

    def __repr__(self):
        return f"LRUStore({self.store})"

    def set(self, key, value):
        self.store[key] = value
        self.store.move_to_end(key)
        if len(self.store) > self.capacity:
            self.store.popitem(last=False)

    def get(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return self.store[key]
        return None

    def get_all(self):
        return self.store
