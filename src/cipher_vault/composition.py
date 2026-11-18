"""Composition root: wire the use cases to SQLite and build the FastAPI app."""

import os
from typing import TYPE_CHECKING

from fastapi import FastAPI

from cipher_vault.application.use_cases import GuessRound, ReadRound, StartRound
from cipher_vault.infrastructure.repository import SQLiteRoundRepository
from cipher_vault.presentation.http import router

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from cipher_vault.application.ports import RoundRepository
    from cipher_vault.domain import Code


class RoundUseCases:
    """The three round use cases sharing one repository."""

    def __init__(
        self,
        repository: RoundRepository,
        id_factory: Callable[[], str] | None = None,
        code_factory: Callable[[], Code] | None = None,
    ) -> None:
        """Build every use case on `repository` with optional factories."""
        self.start = StartRound(repository, id_factory, code_factory)
        self.guess = GuessRound(repository)
        self.read = ReadRound(repository)


def build_round_use_cases(
    path: str | Path | None = None,
    id_factory: Callable[[], str] | None = None,
    code_factory: Callable[[], Code] | None = None,
) -> RoundUseCases:
    """Wire the use cases to the SQLite repository at `path`."""
    database_path = path or os.environ.get(
        "CIPHER_VAULT_DB_PATH", "test-results/cipher-vault.sqlite3"
    )
    return RoundUseCases(SQLiteRoundRepository(database_path), id_factory, code_factory)


def create_app() -> FastAPI:
    """Build the FastAPI application with its routes."""
    app = FastAPI(title="Cipher Vault", docs_url=None, redoc_url=None)
    app.state.round_use_cases = build_round_use_cases()
    app.include_router(router)
    return app
