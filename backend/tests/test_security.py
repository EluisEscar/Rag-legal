import unittest

from fastapi import HTTPException

from app.core.rate_limit import RateLimitMiddleware
from app.core.validation import (
    clean_filename,
    clean_optional_uuid,
    clean_text,
)


class InputValidationTests(unittest.TestCase):
    def test_clean_text_trims_valid_text(self):
        self.assertEqual(
            clean_text("  consulta legal  ", field="pregunta", max_length=50),
            "consulta legal",
        )

    def test_clean_text_rejects_control_characters(self):
        with self.assertRaises(HTTPException) as context:
            clean_text("hola\x00", field="pregunta", max_length=50)

        self.assertEqual(context.exception.status_code, 400)

    def test_clean_text_rejects_oversized_value(self):
        with self.assertRaises(HTTPException) as context:
            clean_text("x" * 51, field="titulo", max_length=50)

        self.assertEqual(context.exception.status_code, 413)

    def test_optional_uuid_rejects_malformed_ids(self):
        with self.assertRaises(HTTPException) as context:
            clean_optional_uuid("conversation-1", field="conversacion_id")

        self.assertEqual(context.exception.status_code, 400)

    def test_filename_strips_path_segments(self):
        self.assertEqual(
            clean_filename(r"..\secretos\contrato.pdf"),
            "contrato.pdf",
        )


class RateLimitTests(unittest.TestCase):
    def test_rate_limit_blocks_after_configured_attempts(self):
        middleware = RateLimitMiddleware(
            app=None,
            request_limit=2,
            request_window_seconds=60,
            auth_attempt_limit=5,
            auth_window_seconds=900,
            max_request_bytes=100,
        )
        attempts = []

        self.assertFalse(middleware._is_limited(attempts, 2, 60, 1.0))
        self.assertFalse(middleware._is_limited(attempts, 2, 60, 2.0))
        self.assertTrue(middleware._is_limited(attempts, 2, 60, 3.0))

    def test_auth_routes_are_detected(self):
        middleware = RateLimitMiddleware(
            app=None,
            request_limit=100,
            request_window_seconds=60,
            auth_attempt_limit=5,
            auth_window_seconds=900,
            max_request_bytes=100,
        )

        self.assertTrue(middleware._is_auth_route("/auth/login"))
        self.assertTrue(middleware._is_auth_route("/login"))
        self.assertFalse(middleware._is_auth_route("/preguntar"))
