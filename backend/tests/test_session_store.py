import time
import unittest

from app.services.session_store import SessionStore


class SessionStoreTests(unittest.TestCase):
    def test_evicts_oldest_session(self):
        store = SessionStore(max_sessions=2, ttl_seconds=60)
        store.set("a", {"value": 1})
        store.set("b", {"value": 2})
        store.set("c", {"value": 3})

        self.assertIsNone(store.get("a"))
        self.assertEqual(store.get("b")["value"], 2)
        self.assertEqual(store.get("c")["value"], 3)

    def test_expires_session(self):
        store = SessionStore(max_sessions=2, ttl_seconds=0.01)
        store.set("a", {"value": 1})
        time.sleep(0.02)

        self.assertIsNone(store.get("a"))
