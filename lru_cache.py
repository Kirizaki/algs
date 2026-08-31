import time
import threading


class LRUCache:
    class Node:
        def __init__(self, key, value, ttl):
            self.key = key
            self.value = value
            self.prev = None
            self.next = None
            self.expires_at = None if not ttl else time.monotonic() + ttl

    def __init__(self, cap):
        self.cap = cap
        self.cache_map = {}
        self.head = LRUCache.Node(-1, -1, None)
        self.tail = LRUCache.Node(-1, -1, None)
        self.head.next = self.tail
        self.tail.prev = self.head
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            node = self.cache_map.get(key, -1)
            if node == -1:
                return -1

            if node.expires_at and node.expires_at < time.monotonic():
                del self.cache_map[key]
                self.remove(node)
                return -1

            self.remove(node)
            self.add(node)
            return node.value

    def put(self, key, value, ttl=None):
        with self.lock:
            if self.cap == 0:
                return

            node = self.cache_map.get(key, None)
            if node is not None:
                node.value = value
                node.expires_at = None if not ttl else time.monotonic() + ttl
                self.remove(node)
            else:
                node = LRUCache.Node(key, value, ttl)
                self.cache_map[key] = node

            self.add(node)
            self.evict_if_needed()

    def remove(self, node):
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

    def add(self, node):
        temp = self.head.next
        node.next = temp
        node.prev = self.head
        temp.prev = node
        self.head.next = node

    def evict_if_needed(self):
        if len(self.cache_map) > self.cap:
            node = self.tail.prev
            del self.cache_map[node.key]
            self.remove(node)
