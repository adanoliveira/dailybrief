from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import RequestFactory, SimpleTestCase
from jwt.exceptions import InvalidTokenError
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.authentication import JWTAuthentication
from apps.accounts.middleware import JWTAuthenticationMiddleware, get_user_from_token


class JWTAuthenticationTests(SimpleTestCase):
    def setUp(self):
        self.backend = JWTAuthentication()

    def test_authenticate_returns_none_without_bearer_token(self):
        request = SimpleNamespace(headers={})

        self.assertIsNone(self.backend.authenticate(request))

    @patch("apps.accounts.authentication.User.objects.get")
    @patch("apps.accounts.authentication.jwt.decode")
    def test_authenticate_returns_user_and_token(self, mock_decode, mock_get):
        fake_user = SimpleNamespace(id=7, username="alice")
        mock_decode.return_value = {"django_user_id": 7}
        mock_get.return_value = fake_user
        request = SimpleNamespace(headers={"Authorization": "Bearer header.payload.signature"})

        user, token = self.backend.authenticate(request)

        self.assertIs(user, fake_user)
        self.assertEqual(token, "header.payload.signature")
        mock_decode.assert_called_once()
        mock_get.assert_called_once_with(id=7)

    @patch("apps.accounts.authentication.jwt.decode")
    def test_authenticate_returns_none_when_payload_has_no_user_id(self, mock_decode):
        mock_decode.return_value = {"sub": "missing-user-id"}
        request = SimpleNamespace(headers={"Authorization": "Bearer valid.token.value"})

        self.assertIsNone(self.backend.authenticate(request))

    @patch("apps.accounts.authentication.jwt.decode")
    def test_authenticate_raises_authentication_failed_for_invalid_token(self, mock_decode):
        mock_decode.side_effect = InvalidTokenError("bad token")
        request = SimpleNamespace(headers={"Authorization": "Bearer invalid.token.value"})

        with self.assertRaises(AuthenticationFailed) as ctx:
            self.backend.authenticate(request)

        self.assertIn("Invalid or expired token", str(ctx.exception))

    @patch("apps.accounts.authentication.User.objects.get")
    @patch("apps.accounts.authentication.jwt.decode")
    def test_authenticate_raises_authentication_failed_when_user_missing(self, mock_decode, mock_get):
        mock_decode.return_value = {"django_user_id": 123}
        mock_get.side_effect = User.DoesNotExist()
        request = SimpleNamespace(headers={"Authorization": "Bearer valid.token.value"})

        with self.assertRaises(AuthenticationFailed):
            self.backend.authenticate(request)


class JWTMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = JWTAuthenticationMiddleware(lambda request: None)

    def test_get_user_from_token_returns_none_without_bearer(self):
        request = self.factory.get("/")
        self.assertIsNone(get_user_from_token(request))

    @patch("apps.accounts.middleware.User.objects.get")
    @patch("apps.accounts.middleware.jwt.decode")
    def test_get_user_from_token_returns_user(self, mock_decode, mock_get):
        fake_user = SimpleNamespace(id=5)
        mock_decode.return_value = {"django_user_id": 5}
        mock_get.return_value = fake_user
        request = self.factory.get("/", HTTP_AUTHORIZATION="Bearer header.payload.signature")

        user = get_user_from_token(request)

        self.assertIs(user, fake_user)

    @patch("apps.accounts.middleware.jwt.decode")
    def test_get_user_from_token_returns_none_for_invalid_token(self, mock_decode):
        mock_decode.side_effect = InvalidTokenError("bad token")
        request = self.factory.get("/", HTTP_AUTHORIZATION="Bearer bad.token.value")

        self.assertIsNone(get_user_from_token(request))

    @patch("apps.accounts.middleware.get_user_from_token")
    def test_process_request_skips_admin_paths(self, mock_get_user):
        request = self.factory.get("/admin/")
        request.user = SimpleNamespace(username="existing")

        self.middleware.process_request(request)

        mock_get_user.assert_not_called()
        self.assertEqual(request.user.username, "existing")

    @patch("apps.accounts.middleware.get_user_from_token")
    def test_process_request_skips_sync_path(self, mock_get_user):
        request = self.factory.get("/api/auth/sync/")
        request.user = SimpleNamespace(username="existing")

        self.middleware.process_request(request)

        mock_get_user.assert_not_called()
        self.assertEqual(request.user.username, "existing")

    @patch("apps.accounts.middleware.get_user_from_token")
    def test_process_request_uses_token_user_when_available(self, mock_get_user):
        token_user = SimpleNamespace(username="token-user")
        mock_get_user.return_value = token_user
        request = self.factory.get("/", HTTP_AUTHORIZATION="Bearer valid.token.value")
        request.user = SimpleNamespace(username="existing")

        self.middleware.process_request(request)

        self.assertEqual(request.user.username, "token-user")

    @patch("apps.accounts.middleware.get_user_from_token")
    def test_process_request_falls_back_to_existing_user(self, mock_get_user):
        mock_get_user.return_value = None
        request = self.factory.get("/")
        request.user = SimpleNamespace(username="existing")

        self.middleware.process_request(request)

        self.assertEqual(request.user.username, "existing")
