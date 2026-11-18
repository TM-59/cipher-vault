# Copyright 2026 TM-59
"""Framework-independent round use cases; the secret is shown only when a round ends."""

import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import uuid4

from cipher_vault.domain import (
    Code,
    GuessScored,
    Round,
    RoundState,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from cipher_vault.application.ports import RoundRepository


class RoundNotFoundError(LookupError):
    """No round exists with the requested identity."""


class RoundConflictError(RuntimeError):
    """The round changed after it was read."""


@dataclass(frozen=True, slots=True)
class RoundView:
    """What a player may see of a round: the secret only once the round is over."""

    round_id: str
    state: RoundState
    history: tuple[GuessScored, ...]
    turns_used: int
    turns_left: int
    secret: Code | None


def _view(round_: Round) -> RoundView:
    state = round_.state
    return RoundView(
        round_.round_id,
        state,
        round_.history,
        round_.turns_used,
        round_.turns_left,
        round_.secret if state is not RoundState.ACTIVE else None,
    )


def _new_code() -> Code:
    return Code(
        (
            secrets.randbelow(6),
            secrets.randbelow(6),
            secrets.randbelow(6),
            secrets.randbelow(6),
        )
    )


class StartRound:
    """Create a round with a new identity and a hidden code, and store it."""

    def __init__(
        self,
        repository: RoundRepository,
        id_factory: Callable[[], str] | None = None,
        code_factory: Callable[[], Code] | None = None,
    ) -> None:
        """Use `repository`, and optional factories for identities and hidden codes."""
        self._repository = repository
        self._id_factory = id_factory if id_factory is not None else (lambda: str(uuid4()))
        self._code_factory = code_factory if code_factory is not None else _new_code

    def execute(self) -> RoundView:
        """Start a round and return its view."""
        round_ = Round(self._id_factory(), self._code_factory())
        self._repository.add(round_)
        return _view(round_)


class ReadRound:
    """Read the view of a stored round."""

    def __init__(self, repository: RoundRepository) -> None:
        """Use `repository` to read rounds."""
        self._repository = repository

    def execute(self, round_id: str) -> RoundView:
        """Return the view of round `round_id`."""
        record = self._repository.get(round_id)
        if record is None:
            raise RoundNotFoundError(round_id)
        return _view(record.round)


class GuessRound:
    """Score a guess in a stored round."""

    def __init__(self, repository: RoundRepository) -> None:
        """Use `repository` to read and save rounds."""
        self._repository = repository

    def execute(self, round_id: str, guess: Code) -> GuessScored:
        """Score `guess`, save, and return the event."""
        record = self._repository.get(round_id)
        if record is None:
            raise RoundNotFoundError(round_id)
        event = record.round.guess(guess)
        if not self._repository.save(record.round, event, record.revision):
            raise RoundConflictError(round_id)
        return event
