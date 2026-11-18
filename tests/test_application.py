"""Use cases against an in-memory repository port."""

from copy import deepcopy
from typing import cast

import pytest

from cipher_vault.application.ports import RoundRecord, RoundRepository
from cipher_vault.application.use_cases import (
    GuessRound,
    ReadRound,
    RoundConflictError,
    RoundNotFoundError,
    RoundView,
    StartRound,
)
from cipher_vault.domain import MAX_GUESSES, Code, GuessScored, Round, RoundState


class MemoryRoundRepository:
    """In-memory RoundRepository with revisions and an injectable rejected save."""

    def __init__(self) -> None:
        """Start empty, accepting saves."""
        self.records: dict[str, RoundRecord] = {}
        self.reject_save = False

    def add(self, round_: Round) -> None:
        """Store a copy of the round at revision 0."""
        self.records[round_.round_id] = RoundRecord(deepcopy(round_), (), 0)

    def get(self, round_id: str) -> RoundRecord | None:
        """Return a copy of the stored record."""
        record = self.records.get(round_id)
        if record is None:
            return None
        return RoundRecord(deepcopy(record.round), record.events, record.revision)

    def save(self, round_: Round, event: GuessScored, expected_revision: int) -> bool:
        """Save when the revision matches and saves are not rejected."""
        record = self.records[round_.round_id]
        if self.reject_save or record.revision != expected_revision:
            return False
        self.records[round_.round_id] = RoundRecord(
            deepcopy(round_), (*record.events, event), record.revision + 1
        )
        return True


def test_req_usecase_start_guess_and_read_hide_the_secret_until_terminal() -> None:
    """REQ-USECASE: start, guess and read keep the secret hidden until the round ends."""
    repository: RoundRepository = MemoryRoundRepository()
    start = StartRound(repository, lambda: "round-1", lambda: Code.parse("0012"))
    started = start.execute()
    assert isinstance(started, RoundView)
    assert started.secret is None
    assert started.turns_left == MAX_GUESSES

    guess = GuessRound(repository)
    first = guess.execute("round-1", Code.parse("0203"))
    active = ReadRound(repository).execute("round-1")
    assert first.round_id == "round-1"
    assert active.secret is None
    assert active.history == (first,)

    won = guess.execute("round-1", Code.parse("0012"))
    terminal = ReadRound(repository).execute("round-1")
    assert won.state is RoundState.WON
    assert terminal.secret == Code.parse("0012")
    assert terminal.history == (first, won)


def test_req_usecase_unknown_round_and_invalid_guess_do_not_persist() -> None:
    """REQ-USECASE: unknown rounds and invalid guesses store nothing."""
    repository = MemoryRoundRepository()
    StartRound(repository, lambda: "round-1", lambda: Code.parse("0012")).execute()
    before = ReadRound(repository).execute("round-1")
    guess = GuessRound(repository)

    with pytest.raises(RoundNotFoundError):
        ReadRound(repository).execute("missing")
    with pytest.raises(RoundNotFoundError):
        guess.execute("missing", Code.parse("0000"))
    with pytest.raises(TypeError):
        guess.execute("round-1", cast("Code", "0012"))

    assert ReadRound(repository).execute("round-1") == before


def test_req_usecase_stale_revision_is_reported_as_a_conflict() -> None:
    """REQ-USECASE: a rejected save is reported as a conflict."""
    repository = MemoryRoundRepository()
    StartRound(repository, lambda: "round-1", lambda: Code.parse("0012")).execute()
    repository.reject_save = True

    with pytest.raises(RoundConflictError):
        GuessRound(repository).execute("round-1", Code.parse("0203"))

    record = repository.get("round-1")
    assert record is not None
    assert record.revision == 0
    assert record.events == ()
