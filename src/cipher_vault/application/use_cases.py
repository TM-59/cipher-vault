import secrets
from collections.abc import Callable
from dataclasses import dataclass
from uuid import uuid4

from cipher_vault.application.ports import RoundRepository
from cipher_vault.domain import (
    Code,
    GuessScored,
    Round,
    RoundState,
)


class RoundNotFound(LookupError):
    """No round exists with the requested identity."""


class RoundConflict(RuntimeError):
    """The round changed after it was read."""


@dataclass(frozen=True, slots=True)
class RoundView:
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
    def __init__(
        self,
        repository: RoundRepository,
        id_factory: Callable[[], str] | None = None,
        code_factory: Callable[[], Code] | None = None,
    ) -> None:
        self._repository = repository
        self._id_factory = id_factory if id_factory is not None else (lambda: str(uuid4()))
        self._code_factory = code_factory if code_factory is not None else _new_code

    def execute(self) -> RoundView:
        round_ = Round(self._id_factory(), self._code_factory())
        self._repository.add(round_)
        return _view(round_)


class ReadRound:
    def __init__(self, repository: RoundRepository) -> None:
        self._repository = repository

    def execute(self, round_id: str) -> RoundView:
        record = self._repository.get(round_id)
        if record is None:
            raise RoundNotFound(round_id)
        return _view(record.round)


class GuessRound:
    def __init__(self, repository: RoundRepository) -> None:
        self._repository = repository

    def execute(self, round_id: str, guess: Code) -> GuessScored:
        record = self._repository.get(round_id)
        if record is None:
            raise RoundNotFound(round_id)
        event = record.round.guess(guess)
        if not self._repository.save(record.round, event, record.revision):
            raise RoundConflict(round_id)
        return event
