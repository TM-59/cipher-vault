import subprocess
import sys
from http import HTTPStatus

from fastapi.testclient import TestClient

from cipher_vault.composition import create_app


def test_req_health_returns_typed_response() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"status": "ok"}


def test_req_core_imports_without_site_packages() -> None:
    subprocess.run(
        [
            sys.executable,
            "-S",
            "-c",
            "import cipher_vault.domain, cipher_vault.application.use_cases",
        ],
        env={"PYTHONPATH": "src"},
        check=True,
        timeout=10,
    )
