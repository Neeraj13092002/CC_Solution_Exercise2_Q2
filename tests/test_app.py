import unittest
from unittest.mock import patch

import redis

from app import app as app_module


class VisitCounterTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    @patch("app.app.redis_client.incr", return_value=7)
    def test_named_endpoints_increment_and_return_the_counter(self, increment):
        for path in ("/increment", "/showCurrentCount"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get_json(), {"visits": 7})

        self.assertEqual(increment.call_count, 2)
        increment.assert_called_with("visits")

    @patch("app.app.redis_client.incr", return_value=8)
    def test_unknown_http_path_also_counts_as_a_visit(self, increment):
        response = self.client.get("/not-a-route")

        self.assertEqual(response.status_code, 404)
        increment.assert_called_once_with("visits")

    @patch(
        "app.app.redis_client.incr",
        side_effect=redis.exceptions.ConnectionError("Redis unavailable"),
    )
    def test_redis_failure_returns_service_unavailable(self, increment):
        response = self.client.get("/increment")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.get_json(),
            {"error": "Visit counter is temporarily unavailable."},
        )
        increment.assert_called_once_with("visits")


if __name__ == "__main__":
    unittest.main()
