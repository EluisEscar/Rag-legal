import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core import auth


class AuthTests(unittest.TestCase):
    def test_rejects_missing_credentials(self):
        with self.assertRaises(HTTPException) as context:
            auth.get_current_user(None)

        self.assertEqual(context.exception.status_code, 401)

    def test_returns_user_from_valid_token(self):
        response = SimpleNamespace(
            user=SimpleNamespace(
                id="user-123",
                email="user@example.com",
            )
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-token",
        )

        with patch.object(
            auth.supabase.auth,
            "get_user",
            return_value=response,
        ):
            user = auth.get_current_user(credentials)

        self.assertEqual(user.id, "user-123")
        self.assertEqual(user.email, "user@example.com")
