import unittest
import requests
from app.code_analysis.analyzer import CodeAnalyzer
from app.core.ai_client import AIEngineClient, scan_sensitive_content


class DummyResponse:
    def __init__(self, status_code, json_data=None, bad_json=False):
        self.status_code = status_code
        self._json_data = json_data
        self._bad_json = bad_json

    def json(self):
        if self._bad_json:
            raise ValueError("Invalid JSON")
        return self._json_data


class TestAIEngineAndPrivacy(unittest.TestCase):
    def test_detects_sensitive_secrets_and_blocks_remote_endpoint(self):
        text = "DB_PASSWORD=MinhaSenhaUltraSecreta123\n-----BEGIN RSA PRIVATE KEY-----\n"
        hits = scan_sensitive_content(text)
        self.assertIn("Chave privada PEM", hits)
        self.assertIn("Credencial hardcoded", hits)

        called_urls = []

        def fake_post(url, headers=None, json=None, timeout=None):
            called_urls.append(url)
            return DummyResponse(200, {"choices": [{"message": {"content": "Resposta local segura"}}]})

        client = AIEngineClient(
            remote_url="https://remote.example/v1",
            local_url="http://localhost:11434/v1",
            local_only=False,
            http_post=fake_post,
        )
        reply, _ = client.request_completion([{"role": "user", "content": text}], has_sensitive_data=True)
        self.assertEqual(reply, "Resposta local segura")
        self.assertEqual(called_urls, ["http://localhost:11434/v1"])

    def test_local_only_mode_never_calls_remote_provider(self):
        called_urls = []

        def fake_post(url, headers=None, json=None, timeout=None):
            called_urls.append(url)
            return DummyResponse(200, {"choices": [{"message": {"content": "OK Ollama"}}]})

        client = AIEngineClient(
            remote_url="https://remote.example/v1",
            local_url="http://localhost:11434/v1",
            local_only=True,
            http_post=fake_post,
        )
        self.assertIn("somente local", client.describe_privacy_mode())
        reply, _ = client.request_completion([{"role": "user", "content": "oi"}])
        self.assertEqual(reply, "OK Ollama")
        self.assertEqual(called_urls, ["http://localhost:11434/v1"])

    def test_fallback_from_remote_failures_to_local_ollama(self):
        failure_cases = [
            lambda *a, **kw: DummyResponse(500),
            lambda *a, **kw: DummyResponse(429),
            lambda *a, **kw: DummyResponse(200, bad_json=True),
            lambda *a, **kw: DummyResponse(200, {"choices": []}),
            lambda *a, **kw: DummyResponse(200, {"choices": [{"message": {"content": "   "}}]}),
            lambda *a, **kw: (_ for _ in ()).throw(requests.Timeout("timeout")),
            lambda *a, **kw: (_ for _ in ()).throw(requests.ConnectionError("dns fail")),
        ]

        for remote_behavior in failure_cases:
            def fake_post(url, headers=None, json=None, timeout=None, rb=remote_behavior):
                if "remote.example" in url:
                    return rb(url, headers=headers, json=json, timeout=timeout)
                return DummyResponse(200, {"choices": [{"message": {"content": "Fallback local OK"}}]})

            client = AIEngineClient(
                remote_url="https://remote.example/v1",
                local_url="http://localhost:11434/v1",
                local_only=False,
                http_post=fake_post,
            )
            reply, errors = client.request_completion([{"role": "user", "content": "teste"}])
            self.assertEqual(reply, "Fallback local OK")
            self.assertEqual(len(errors), 1)

    def test_offline_static_fallback_and_cancellation(self):
        def failing_post(url, headers=None, json=None, timeout=None):
            raise requests.ConnectionError("offline")

        client = AIEngineClient(
            remote_url="https://remote.example/v1",
            local_url="http://localhost:11434/v1",
            local_only=False,
            http_post=failing_post,
        )
        reply, errors = client.request_completion([{"role": "user", "content": "analise"}])
        self.assertIsNone(reply)
        self.assertEqual(len(errors), 2)

        offline = client.build_offline_diagnostics(
            [{"name": "bad.sql", "extension": ".sql", "content": "DELETE FROM users;"}],
            CodeAnalyzer(),
            warnings=errors,
        )
        self.assertIn("Diagnóstico Local Offline", offline)
        self.assertIn("DELETE sem cláusula WHERE", offline)

        # Cancelamento antes da requisição
        cancelled_reply, cancelled_errors = client.request_completion(
            [{"role": "user", "content": "cancelar"}],
            cancelled_fn=lambda: True,
        )
        self.assertIsNone(cancelled_reply)
        self.assertIn("cancelada", cancelled_errors[0].lower())


if __name__ == "__main__":
    unittest.main()
