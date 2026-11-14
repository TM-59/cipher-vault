from copy import deepcopy

import pytest

from cipher_vault.application.ports import RoundRecord, RoundRepository
from cipher_vault.application.use_cases import (
    GuessRound,
    ReadRound,
    RoundConflict,
    RoundNotFound,
    RoundView,
    StartRound,
)
from cipher_vault.domain import Code, GuessScored, Round, RoundState


class MemoryRoundRepository:
    def __init__(self) -> None:
        self.records: dict[str, RoundRecord] = {}
        self.reject_save = False

    def add(self, round_: Round) -> None:
        self.records[round_.round_id] = RoundRecord(deepcopy(round_), (), 0)

    def get(self, round_id: str) -> RoundRecord | None:
        record = self.records.get(round_id)
        if record is None:
            return None
        return RoundRecord(deepcopy(record.round), record.events, record.revision)

    def save(self, round_: Round, event: GuessScored, expected_revision: int) -> bool:
        record = self.records[round_.round_id]
        if self.reject_save or record.revision != expected_revision:
            return False
        self.records[round_.round_id] = RoundRecord(
            deepcopy(round_), (*record.events, event), record.revision + 1
        )
        return True


def test_REQ_USECASE_start_guess_and_read_hide_the_secret_until_terminal() -> None:
    repository: RoundRepository = MemoryRoundRepository()
    start = StartRound(repository, lambda: "round-1", lambda: Code.parse("0012"))
    started = start.execute()
    assert isinstance(started, RoundView)
    assert started.secret is None and started.turns_left == 8

    guess = GuessRound(repository)
    first = guess.execute("round-1", Code.parse("0203"))
    active = ReadRound(repository).execute("round-1")
    assert first.round_id == "round-1"
    assert active.secret is None and active.history == (first,)

    won = guess.execute("round-1", Code.parse("0012"))
    terminal = ReadRound(repository).execute("round-1")
    assert won.state is RoundState.WON
    assert terminal.secret == Code.parse("0012")
    assert terminal.history == (first, won)


def test_REQ_USECASE_unknown_round_and_invalid_guess_do_not_persist() -> None:
    repository = MemoryRoundRepository()
    StartRound(repository, lambda: "round-1", lambda: Code.parse("0012")).execute()
    before = ReadRound(repository).execute("round-1")
    guess = GuessRound(repository)

    with pytest.raises(RoundNotFound):
        ReadRound(repository).execute("missing")
    with pytest.raises(RoundNotFound):
        guess.execute("missing", Code.parse("0000"))
    with pytest.raises(TypeError):
        guess.execute("round-1", "0012")  # type: ignore[arg-type]

    assert ReadRound(repository).execute("round-1") == before


def test_REQ_USECASE_stale_revision_is_reported_as_a_conflict() -> None:
    repository = MemoryRoundRepository()
    StartRound(repository, lambda: "round-1", lambda: Code.parse("0012")).execute()
    repository.reject_save = True

    with pytest.raises(RoundConflict):
        GuessRound(repository).execute("round-1", Code.parse("0203"))

    record = repository.get("round-1")
    assert record is not None
    assert record.revision == 0 and record.events == ()
