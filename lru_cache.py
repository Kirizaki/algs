import threading
import time

class LRUCache:
    class _Node:
        def __init__(self, key=None, value=None, ttl=None):
            self.key = key
            self.value = value
            self.prev = None
            self.next = None
            self.expires_at = ttl if ttl is None else time.monotonic() + ttl

    def __init__(self, capacity):
        self.capacity = capacity
        self._head = LRUCache._Node()
        self._tail = LRUCache._Node()
        self._head.next = self._tail
        self._tail.prev = self._head
        self.hashmap = {}
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            node = self.hashmap.get(key, None)

            if node is None:
                return None

            if self._is_expired(node):
                del self.hashmap[key]
                self._delete_at(node)
                return None

            self._make_mru(node)
            
            return node.value

    def _is_expired(self, node):
        return node.expires_at is not None and time.monotonic() > node.expires_at

    def _make_mru(self, node):
        self._delete_at(node)
        self._move_to_mru(node)

    def _delete_at(self, node):
        # update adjacent
        node.prev.next = node.next
        node.next.prev = node.prev

        node.next = None
        node.prev = None

    def _move_to_mru(self, node):
        node.next = self._head.next
        node.prev = self._head
        self._head.next.prev = node
        self._head.next = node

    def put(self, key, value, ttl=None):
        with self.lock:
            if key in self.hashmap:  # cache hit
                node = self.hashmap[key]
                node.value = value
                node.expires_at = ttl if ttl is None else time.monotonic() + ttl
                self._delete_at(node)
            else:                    # cache miss
                node = LRUCache._Node(key, value, ttl)
                self.hashmap[key] = node

            self._move_to_mru(node)
            self._evict_if_needed()

    def _evict_if_needed(self):
        if len(self.hashmap) > self.capacity:
            self._evict_lru()

    def _evict_lru(self):
        del self.hashmap[self._tail.prev.key]
        self._delete_at(self._tail.prev)

