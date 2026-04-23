from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.aiproviders.services import AIProviderService, EmbeddingResponse, LLMResponse


def build_chat_response(content="ok", prompt_tokens=100, completion_tokens=40):
    usage = SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(
        choices=[choice],
        usage=usage,
        model_dump=lambda: {"id": "chatcmpl-test"},
    )


def build_embedding_response(vectors, prompt_tokens=50):
    usage = SimpleNamespace(prompt_tokens=prompt_tokens, total_tokens=prompt_tokens)
    data = [SimpleNamespace(embedding=vector) for vector in vectors]
    return SimpleNamespace(
        data=data,
        usage=usage,
        model_dump=lambda: {"id": "emb-test"},
    )


class AIProviderServiceRoutingTests(SimpleTestCase):
    def setUp(self):
        self.service = AIProviderService()

    def test_call_llm_returns_error_when_config_missing(self):
        with patch.object(self.service, "get_provider_config", return_value=None):
            response = self.service.call_llm("prompt", operation="summarization")

        self.assertFalse(response.success)
        self.assertEqual(response.provider, "none")
        self.assertIn("No active provider configuration", response.error_message)

    def test_call_llm_routes_to_openai_handler(self):
        config = SimpleNamespace(provider="openai", model="gpt-4.1-mini")
        expected = LLMResponse(
            content="answer",
            success=True,
            usage={"total_tokens": 10},
            response_time=0.1,
            provider="openai",
            model="gpt-4.1-mini",
        )

        with patch.object(self.service, "get_provider_config", return_value=config), patch.object(
            self.service, "_call_openai", return_value=expected
        ) as mock_call:
            response = self.service.call_llm("prompt", operation="summarization", max_tokens=200)

        self.assertIs(response, expected)
        mock_call.assert_called_once()

    def test_call_llm_returns_error_for_unsupported_provider(self):
        config = SimpleNamespace(provider="unknown", model="x-model")
        with patch.object(self.service, "get_provider_config", return_value=config):
            response = self.service.call_llm("prompt", operation="summarization")

        self.assertFalse(response.success)
        self.assertEqual(response.provider, "unknown")
        self.assertIn("Unsupported provider", response.error_message)

    def test_generate_embedding_rejects_empty_texts(self):
        response = self.service.generate_embedding(["", "   "])

        self.assertIsInstance(response, EmbeddingResponse)
        self.assertFalse(response.success)
        self.assertIn("No valid texts provided", response.error_message)

    def test_generate_embedding_rejects_batch_over_limit(self):
        response = self.service.generate_embedding(["x"] * 2049)

        self.assertFalse(response.success)
        self.assertIn("Too many texts", response.error_message)

    def test_generate_embedding_rejects_unsupported_provider(self):
        config = SimpleNamespace(provider="anthropic", model="claude-3")
        with patch.object(self.service, "get_provider_config", return_value=config):
            response = self.service.generate_embedding(["hello"], operation="embedding_generation")

        self.assertFalse(response.success)
        self.assertIn("Embedding not supported", response.error_message)


class OpenAIInvocationTests(SimpleTestCase):
    def setUp(self):
        self.service = AIProviderService()
        self.service._openai_client = MagicMock()

    @patch.object(AIProviderService, "_log_usage")
    def test_call_openai_omits_temperature_and_max_tokens_for_reasoning_models(self, mock_log):
        self.service._openai_client.chat.completions.create.return_value = build_chat_response()

        response = self.service._call_openai(
            prompt="prompt",
            model="o3",
            max_tokens=900,
            temperature=0.7,
            operation="summarization",
            start_time=0.0,
        )

        called_kwargs = self.service._openai_client.chat.completions.create.call_args.kwargs
        self.assertNotIn("temperature", called_kwargs)
        self.assertNotIn("max_tokens", called_kwargs)
        self.assertTrue(response.success)
        self.assertEqual(response.provider, "openai")
        mock_log.assert_called_once()

    @patch.object(AIProviderService, "_log_usage")
    def test_call_openai_sets_high_token_budget_for_gpt41_content_extraction(self, mock_log):
        self.service._openai_client.chat.completions.create.return_value = build_chat_response()

        self.service._call_openai(
            prompt="prompt",
            model="gpt-4.1-mini",
            max_tokens=None,
            temperature=0.2,
            operation="content_extraction",
            start_time=0.0,
        )

        called_kwargs = self.service._openai_client.chat.completions.create.call_args.kwargs
        self.assertEqual(called_kwargs["max_tokens"], 30000)
        self.assertEqual(called_kwargs["temperature"], 0.2)
        mock_log.assert_called_once()

    @patch.object(AIProviderService, "_log_usage")
    def test_call_openai_includes_estimated_cost_in_usage(self, mock_log):
        self.service._openai_client.chat.completions.create.return_value = build_chat_response(
            prompt_tokens=1000,
            completion_tokens=1000,
        )

        response = self.service._call_openai(
            prompt="prompt",
            model="gpt-4o-mini",
            max_tokens=200,
            temperature=0.2,
            operation="summarization",
            start_time=0.0,
        )

        self.assertTrue(response.success)
        self.assertIn("estimated_cost", response.usage)
        self.assertIn("total_cost", response.usage)
        self.assertAlmostEqual(response.usage["estimated_cost"], 0.00075, places=8)

    @patch.object(AIProviderService, "_log_usage")
    def test_call_openai_returns_failure_when_client_errors(self, mock_log):
        self.service._openai_client.chat.completions.create.side_effect = RuntimeError("provider down")

        response = self.service._call_openai(
            prompt="prompt",
            model="gpt-4.1-mini",
            max_tokens=100,
            temperature=0.1,
            operation="summarization",
            start_time=0.0,
        )

        self.assertFalse(response.success)
        self.assertIn("provider down", response.error_message)
        mock_log.assert_called_once()

    @patch.object(AIProviderService, "_log_usage")
    def test_generate_openai_embedding_passes_dimensions_for_supported_model(self, mock_log):
        self.service._openai_client.embeddings.create.return_value = build_embedding_response([[0.1, 0.2], [0.3, 0.4]])

        response = self.service._generate_openai_embedding(
            texts=["first", "second"],
            model="text-embedding-3-small",
            operation="embedding_generation",
            start_time=0.0,
            dimensions=128,
        )

        called_kwargs = self.service._openai_client.embeddings.create.call_args.kwargs
        self.assertEqual(called_kwargs["dimensions"], 128)
        self.assertTrue(response.success)
        self.assertEqual(len(response.embeddings), 2)
        mock_log.assert_called_once()


class UsageLoggingTests(SimpleTestCase):
    def setUp(self):
        self.service = AIProviderService()

    @patch("apps.aiproviders.services.AIProviderUsage.objects.create")
    def test_log_usage_calculates_gpt41_mini_cost(self, mock_create):
        self.service._log_usage(
            provider="openai",
            model="gpt-4.1-mini",
            operation="summarization",
            usage={"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500},
            response_time=1.25,
            success=True,
        )

        self.assertTrue(mock_create.called)
        estimated_cost = mock_create.call_args.kwargs["estimated_cost"]
        self.assertEqual(estimated_cost, Decimal("0.0012"))

    @patch("apps.aiproviders.services.AIProviderUsage.objects.create")
    def test_log_usage_uses_usage_estimated_cost_when_provided(self, mock_create):
        self.service._log_usage(
            provider="openai",
            model="gpt-4o-mini",
            operation="summarization",
            usage={
                "prompt_tokens": 1000,
                "completion_tokens": 1000,
                "total_tokens": 2000,
                "estimated_cost": 0.00075,
            },
            response_time=1.0,
            success=True,
        )

        self.assertTrue(mock_create.called)
        estimated_cost = mock_create.call_args.kwargs["estimated_cost"]
        self.assertEqual(estimated_cost, Decimal("0.00075"))
