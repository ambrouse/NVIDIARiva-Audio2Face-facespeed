from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_readme_documents_current_runtime_contract() -> None:
    readme = read("README.md")
    required = [
        "http://127.0.0.1:6300/",
        "facespeed-riva-docker",
        "facespeed-riva-backend",
        "127.0.0.1:6051",
        "127.0.0.1:6052",
        "http://127.0.0.1:8005",
        "http://127.0.0.1:8006",
        "http://127.0.0.1:8007/v1",
        "tests/benchmarks/REPORT-2026-05-25-rag-voice.md",
        "tests/nginx-proxy/test-nginx-proxy-20260526-v1.md",
        "dev by ambrouse",
    ]
    for value in required:
        assert value in readme


def test_env_example_uses_direct_provider_ports() -> None:
    env = read(".env.example")
    assert "DOCLING_API_BASE_URL=http://127.0.0.1:8005" in env
    assert "EMBEDDING_API_BASE_URL=http://127.0.0.1:8006" in env
    assert "LLM_API_BASE_URL=http://127.0.0.1:8007/v1" in env
    assert "VOICE_CHAT_TTS_MAX_CHARS=150" in env
    assert "DOCLING_API_BASE_URL=http://127.0.0.1:6105" not in env
    assert "EMBEDDING_API_BASE_URL=http://127.0.0.1:6106" not in env


def test_nginx_proxy_is_documented_and_configured() -> None:
    compose = read("docker-compose.yml")
    nginx = read("docker/nginx/facespeed.conf.template")
    assert "facespeed-nginx" in compose
    assert "FACESPEED_PROXY_PORT" in compose
    assert "proxy_pass http://${BACKEND_HOST}:${BACKEND_PORT}" in nginx
    assert "proxy_pass http://${FRONTEND_HOST}:${FRONTEND_PORT}" in nginx
    assert "proxy_set_header Upgrade" in nginx
