import json
from types import SimpleNamespace
from unittest.mock import patch

from django.http import HttpRequest
from django.test import RequestFactory, SimpleTestCase, override_settings

from apps.core import api_utils


class JwtUtilitiesTests(SimpleTestCase):
    def test_create_jwt_token_returns_decodable_token(self):
        user = SimpleNamespace(id=42, email="user@example.com")

        token = api_utils.create_jwt_token(user)
        payload = api_utils.jwt.decode(
            token,
            api_utils.settings.SECRET_KEY,
            algorithms=["HS256"],
        )

        self.assertEqual(payload["user_id"], 42)
        self.assertEqual(payload["django_user_id"], 42)
        self.assertEqual(payload["email"], "user@example.com")

    def test_authenticate_request_rejects_missing_header(self):
        request = HttpRequest()
        request.META = {}

        ok, user, error = api_utils.authenticate_request(request)

        self.assertFalse(ok)
        self.assertIsNone(user)
        self.assertEqual(error, "No Authorization header")

    def test_authenticate_request_rejects_malformed_token(self):
        request = HttpRequest()
        request.META = {"HTTP_AUTHORIZATION": "Bearer not.a.jwt.with.four.parts"}

        ok, user, error = api_utils.authenticate_request(request)

        self.assertFalse(ok)
        self.assertIsNone(user)
        self.assertIn("Invalid token format", error)

    @patch("apps.core.api_utils.User.objects.get")
    @patch("apps.core.api_utils.jwt.decode")
    def test_authenticate_request_supports_legacy_user_id_key(self, mock_decode, mock_get):
        request = HttpRequest()
        request.META = {"HTTP_AUTHORIZATION": "Bearer valid.jwt.token"}
        fake_user = SimpleNamespace(id=9, is_staff=False)
        mock_decode.return_value = {"user_id": 9}
        mock_get.return_value = fake_user

        ok, user, error = api_utils.authenticate_request(request)

        self.assertTrue(ok)
        self.assertIs(user, fake_user)
        self.assertIsNone(error)

    @patch("apps.core.api_utils.User.objects.get")
    @patch("apps.core.api_utils.jwt.decode")
    def test_authenticate_request_handles_missing_user(self, mock_decode, mock_get):
        request = HttpRequest()
        request.META = {"HTTP_AUTHORIZATION": "Bearer valid.jwt.token"}
        mock_decode.return_value = {"django_user_id": 333}
        mock_get.side_effect = api_utils.User.DoesNotExist()

        ok, user, error = api_utils.authenticate_request(request)

        self.assertFalse(ok)
        self.assertIsNone(user)
        self.assertEqual(error, "User not found")


class CorsAndResponseTests(SimpleTestCase):
    @override_settings(CORS_ALLOWED_ORIGINS=["https://allowed.example", "https://fallback.example"])
    def test_resolve_cors_origin_prefers_request_origin(self):
        request = HttpRequest()
        request.META = {"HTTP_ORIGIN": "https://allowed.example"}

        origin = api_utils._resolve_cors_origin(request)

        self.assertEqual(origin, "https://allowed.example")

    @override_settings(CORS_ALLOWED_ORIGINS=["https://fallback.example"])
    def test_resolve_cors_origin_falls_back_to_first_allowlisted(self):
        request = HttpRequest()
        request.META = {"HTTP_ORIGIN": "https://not-allowed.example"}

        origin = api_utils._resolve_cors_origin(request)

        self.assertEqual(origin, "https://fallback.example")

    @override_settings(CORS_ALLOWED_ORIGINS=["https://frontend.example"])
    def test_create_response_adds_cors_headers(self):
        request = HttpRequest()
        request.META = {"HTTP_ORIGIN": "https://frontend.example"}

        response = api_utils.create_response({"ok": True}, request=request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], "https://frontend.example")
        self.assertEqual(response["Access-Control-Allow-Methods"], "GET, POST, PUT, DELETE, OPTIONS")
        self.assertEqual(response["Vary"], "Origin")

    @override_settings(CORS_ALLOWED_ORIGINS=["https://frontend.example"])
    def test_handle_options_request_sets_preflight_headers(self):
        request = HttpRequest()
        request.META = {"HTTP_ORIGIN": "https://frontend.example"}

        response = api_utils.handle_options_request("GET, OPTIONS", request=request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], "https://frontend.example")
        self.assertEqual(response["Access-Control-Allow-Methods"], "GET, OPTIONS")
        self.assertEqual(response["Access-Control-Max-Age"], "86400")

    def test_create_success_response_wraps_payload(self):
        response = api_utils.create_success_response({"id": 1}, message="saved")
        payload = json.loads(response.content)

        self.assertEqual(payload["data"], {"id": 1})
        self.assertTrue(payload["success"])
        self.assertEqual(payload["message"], "saved")


class RequestBodyAndPaginationTests(SimpleTestCase):
    def test_parse_request_body_returns_empty_dict_for_empty_body(self):
        request = SimpleNamespace(body=b"")

        data, error = api_utils.parse_request_body(request)

        self.assertEqual(data, {})
        self.assertIsNone(error)

    def test_parse_request_body_rejects_invalid_json(self):
        request = SimpleNamespace(body=b'{"bad": }')

        data, error = api_utils.parse_request_body(request)
        payload = json.loads(error.content)

        self.assertIsNone(data)
        self.assertEqual(error.status_code, 400)
        self.assertEqual(payload["error"], "Invalid JSON in request body")
        self.assertIn("json_error", payload["details"])

    def test_paginate_response_clamps_page_and_page_size(self):
        result = api_utils.paginate_response(
            list(range(1, 21)),
            page=999,
            page_size=500,
            max_page_size=7,
        )

        self.assertEqual(result["pagination"]["page_size"], 7)
        self.assertEqual(result["pagination"]["total_pages"], 3)
        self.assertEqual(result["pagination"]["page"], 3)
        self.assertEqual(result["items"], [15, 16, 17, 18, 19, 20])


class ApiViewDecoratorTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(CORS_ALLOWED_ORIGINS=["https://client.example"])
    def test_options_request_is_handled_before_view_execution(self):
        called = {"value": False}

        @api_utils.api_view(["GET"])
        def sample_view(request):
            called["value"] = True
            return api_utils.create_response({"ok": True}, request=request)

        request = self.factory.options("/", HTTP_ORIGIN="https://client.example")
        response = sample_view(request)

        self.assertFalse(called["value"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Methods"], "GET, OPTIONS")

    def test_method_not_allowed_returns_405(self):
        @api_utils.api_view(["GET"])
        def sample_view(request):
            return api_utils.create_response({"ok": True}, request=request)

        response = sample_view(self.factory.post("/"))
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(payload["error"], "Method POST not allowed")
        self.assertEqual(payload["details"]["allowed_methods"], ["GET"])

    @patch("apps.core.api_utils.authenticate_request")
    def test_authentication_failure_returns_401(self, mock_authenticate):
        mock_authenticate.return_value = (False, None, "No Authorization header")

        @api_utils.api_view(["GET"])
        def sample_view(request):
            return api_utils.create_response({"ok": True}, request=request)

        response = sample_view(self.factory.get("/"))
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(payload["error"], "Authentication failed")

    @patch("apps.core.api_utils.authenticate_request")
    def test_staff_required_rejects_non_staff_users(self, mock_authenticate):
        mock_authenticate.return_value = (True, SimpleNamespace(is_staff=False), None)

        @api_utils.api_view(["GET"], staff_required=True)
        def staff_view(request):
            return api_utils.create_response({"ok": True}, request=request)

        response = staff_view(self.factory.get("/"))
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(payload["error_code"], "INSUFFICIENT_PERMISSIONS")

    @patch("apps.core.api_utils.authenticate_request")
    @override_settings(DEBUG=True)
    def test_skip_auth_dev_allows_request_when_flag_is_set(self, mock_authenticate):
        @api_utils.api_view(["GET"], skip_auth_dev=True)
        def dev_view(request):
            return api_utils.create_response({"ok": True}, request=request)

        request = self.factory.get("/")
        request.skip_auth_for_dev = True
        response = dev_view(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["ok"], True)
        mock_authenticate.assert_not_called()

    @override_settings(DEBUG=False)
    def test_internal_error_is_sanitized_outside_debug_mode(self):
        @api_utils.api_view(["GET"], authenticate=False)
        def exploding_view(request):
            raise RuntimeError("kaboom")

        response = exploding_view(self.factory.get("/"))
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(payload["error_code"], "INTERNAL_ERROR")
        self.assertEqual(payload["error"], "An internal error occurred. Please try again.")
