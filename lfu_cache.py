import time
import threading

class LFUCache:
    class Node:
        def __init__(self, key, value, ttl):
            self.key = key
            self.value = value
            self.expires_at = None if not ttl else time.monotonic() + ttl
            self.cnt = 1
            self.prev = None
            self.next = None

    def __init__(self, cap):
        self.cap = cap
        self.cache_map = {}
        self.freq_map = {}
        self.min_freq = 0
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

            self.update_freq(node)
            return node.value

    def put(self, key, value, ttl=None):
        with self.lock:
            node = self.cache_map.get(key, -1)
            if node != -1:
                node.value = value
                node.ttl = None if not ttl else time.monotonic() + ttl
                self.update_freq(node)
            else:
                self.evict_if_needed()
                self.min_freq = 1
                node = LFUCache.Node(key, value, ttl)
                self.cache_map[key] = node
                self.add(node, self.min_freq)

    def update_freq(self, node):
        old = node.cnt
        node.cnt += 1
        self.remove(node)
        if self.freq_map[old][0].next is self.freq_map[old][1]:
            del self.freq_map[old]
            if self.min_freq == old:
                self.min_freq += 1

        self.add(node, node.cnt)

    def remove(self, node):
        p = node.prev
        n = node.next
        p.next = n
        n.prev = p

    def add(self, node, freq):
        if freq not in self.freq_map:
            h = LFUCache.Node(-1, -1, None)
            t = LFUCache.Node(-1, -1, None)
            h.next = t
            t.prev = h
            self.freq_map[freq] = (h, t)

        head = self.freq_map[freq][0]
        temp = head.next
        node.next = temp
        node.prev = head
        head.next = node
        temp.prev = node

    def evict_if_needed(self):
        if len(self.cache_map) == self.cap:
            n = self.freq_map[self.min_freq][1].prev
            del self.cache_map[n.key]
            self.remove(n)
            if self.freq_map[self.min_freq][0].next is self.freq_map[self.min_freq][1]:
                del self.freq_map[self.min_freq]

