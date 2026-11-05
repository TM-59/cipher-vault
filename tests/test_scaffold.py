import subprocess
import sys

from fastapi.testclient import TestClient

from cipher_vault.composition import create_app


def test_REQ_HEALTH_returns_typed_response() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_REQ_CORE_imports_without_site_packages() -> None:
    subprocess.run(
        [sys.executable, "-S", "-c", "import cipher_vault.domain, cipher_vault.application"],
        env={"PYTHONPATH": "src"},
        check=True,
        timeout=10,
    )
