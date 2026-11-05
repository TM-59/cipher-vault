from fastapi import FastAPI

from cipher_vault.presentation.http import router


def create_app() -> FastAPI:
    app = FastAPI(title="Cipher Vault", docs_url=None, redoc_url=None)
    app.include_router(router)
    return app
